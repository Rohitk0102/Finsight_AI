"""
EnsemblePredictor v2 — production-grade, no training in the API path.

Rules enforced here:
  • Models are ONLY loaded from disk (pre-trained by Celery tasks).
  • If a model artefact is absent, _naive_predict() is used as fallback.
  • Prophet inference uses pre-computed forecast ratios from metadata.json.
  • FinBERT sentiment is read from Supabase ticker_sentiment (pre-computed).
  • Sentiment adjustment:  final_price *= (1 + sentiment_score * 0.02)
  • Confidence = weighted combination of model agreement + MAPE + RSI signal.
  • Structured logging on every prediction with ticker, model_version, latency_ms.
"""

from __future__ import annotations

import time
import asyncio
import numpy as np
import pandas as pd
import yfinance as yf
import joblib
from datetime import datetime, timezone
from typing import Optional
from pathlib import Path
from loguru import logger

from app.schemas.stock import (
    StockPrediction, Signal, RiskLabel, TechnicalIndicators,
)
from app.ml.utils.feature_engineering import (
    compute_features, get_latest_features, LSTM_FEATURE_COLS,
)
from app.ml.models.model_store import (
    load_metadata, model_file, get_model_version, composite_version,
)
from app.ml.models.lstm_trainer import build_lstm, SEQ_LEN
from app.ml.signals.market_regime import detect_regime
from app.schemas.user import RiskProfile, InvestmentHorizon

# ── Weights & thresholds ──────────────────────────────────────────────────────

ENSEMBLE_WEIGHTS = {"xgboost": 0.40, "prophet": 0.35, "lstm": 0.25}

RISK_MULTIPLIERS = {
    RiskProfile.CONSERVATIVE: 0.7,
    RiskProfile.MODERATE: 1.0,
    RiskProfile.AGGRESSIVE: 1.3,
}

_SIGNAL_THRESHOLDS = {
    RiskProfile.CONSERVATIVE: 3.0,
    RiskProfile.MODERATE: 2.0,
    RiskProfile.AGGRESSIVE: 1.0,
}

# Top feature descriptions for human-readable factors
_FEATURE_LABELS: dict[str, str] = {
    "rsi": "RSI",
    "macd_hist": "MACD histogram",
    "volatility_20d": "20-day volatility",
    "return_5d": "5-day momentum",
    "bb_width": "Bollinger Band width",
    "stoch_k": "Stochastic oscillator",
    "volume_ratio": "Volume vs average",
    "ema_20": "EMA-20 trend",
    "dist_from_52w_high": "Distance from 52-week high",
    "dist_from_52w_low": "Distance from 52-week low",
}


class EnsemblePredictor:

    def __init__(self) -> None:
        # {ticker: (model_version_str, models_dict)}
        # Version tag is checked on every call; stale entries are evicted automatically.
        self._xgb_cache: dict[str, tuple[str, dict]] = {}

    async def predict(
        self,
        ticker: str,
        risk_profile: str = RiskProfile.MODERATE,
        horizon: str = InvestmentHorizon.MEDIUM,
        sentiment_score: float = 0.0,
    ) -> StockPrediction:
        t0 = time.perf_counter()

        df = await asyncio.to_thread(self._fetch_data, ticker)
        if df.empty or len(df) < 60:
            raise ValueError(f"Insufficient historical data for {ticker}")

        featured_df = compute_features(df)
        technicals = get_latest_features(df)
        current_price = float(df["Close"].iloc[-1])

        # ── Per-model predictions ─────────────────────────────────────────────
        xgb_pred = self._xgboost_predict(ticker, featured_df)
        prophet_pred = self._prophet_predict(ticker, df, current_price)
        lstm_pred = self._lstm_predict(ticker, featured_df, current_price)

        # ── Weighted ensemble ─────────────────────────────────────────────────
        w = ENSEMBLE_WEIGHTS
        raw_1d = w["xgboost"] * xgb_pred["1d"] + w["prophet"] * prophet_pred["1d"] + w["lstm"] * lstm_pred["1d"]
        raw_7d = w["xgboost"] * xgb_pred["7d"] + w["prophet"] * prophet_pred["7d"] + w["lstm"] * lstm_pred["7d"]
        raw_30d = w["xgboost"] * xgb_pred["30d"] + w["prophet"] * prophet_pred["30d"] + w["lstm"] * lstm_pred["30d"]

        # ── Sentiment adjustment ──────────────────────────────────────────────
        # Bounded to ±4% price shift even at extreme sentiment
        adj_factor = 1.0 + float(np.clip(sentiment_score, -1.0, 1.0)) * 0.02
        pred_1d  = round(raw_1d  * adj_factor, 2)
        pred_7d  = round(raw_7d  * adj_factor, 2)
        pred_30d = round(raw_30d * adj_factor, 2)

        # ── Supporting signals ────────────────────────────────────────────────
        regime = detect_regime(df)
        confidence = self._compute_confidence(xgb_pred, prophet_pred, lstm_pred, technicals, ticker)
        risk_score = self._compute_risk_score(featured_df, risk_profile)
        signal = self._determine_signal(pred_7d, current_price, risk_score, risk_profile, regime)
        risk_label = self._risk_label(risk_score)
        factors = self._build_factors(ticker, featured_df, technicals, signal, pred_7d, current_price, sentiment_score, regime)
        model_version = composite_version(ticker)

        latency_ms = round((time.perf_counter() - t0) * 1000, 1)
        logger.info(
            f"Prediction complete",
            extra={
                "ticker": ticker,
                "model_version": model_version,
                "signal": signal,
                "confidence": confidence,
                "latency_ms": latency_ms,
            },
        )

        return StockPrediction(
            ticker=ticker,
            name=ticker,
            current_price=current_price,
            predicted_1d=pred_1d,
            predicted_7d=pred_7d,
            predicted_30d=pred_30d,
            confidence=round(confidence, 4),
            signal=signal,
            risk_score=round(risk_score, 2),
            risk_label=risk_label,
            sentiment_score=round(float(sentiment_score), 4),
            regime=regime,
            model_version=model_version,
            factors=factors,
            technicals=TechnicalIndicators(**{
                k: (round(v, 4) if v is not None else None)
                for k, v in technicals.items()
                if k in TechnicalIndicators.model_fields
            }),
            generated_at=datetime.now(timezone.utc),
        )

    # ── Data fetching ─────────────────────────────────────────────────────────

    def _fetch_data(self, ticker: str) -> pd.DataFrame:
        try:
            t = yf.Ticker(ticker)
            df = t.history(period="2y", interval="1d")
            df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
            logger.debug(f"Fetched {len(df)} rows for {ticker}", extra={"ticker": ticker})
            return df
        except Exception as exc:
            logger.error(f"Data fetch error for {ticker}: {exc}", extra={"ticker": ticker})
            return pd.DataFrame()

    # ── XGBoost (load from disk, no training) ────────────────────────────────

    def _xgboost_predict(self, ticker: str, df: pd.DataFrame) -> dict:
        try:
            from xgboost import XGBRegressor

            pkl = model_file("xgb", ticker, ".pkl")
            if not pkl.exists():
                logger.warning(
                    f"XGBoost model not found for {ticker}, using naive fallback",
                    extra={"ticker": ticker, "model_version": "none"},
                )
                return self._naive_predict(df)

            current_version = get_model_version("xgb", ticker)
            cached = self._xgb_cache.get(ticker)
            if cached is None or cached[0] != current_version:
                models = joblib.load(pkl)
                self._xgb_cache[ticker] = (current_version, models)
                logger.info(
                    f"XGBoost model loaded",
                    extra={"ticker": ticker, "model_version": current_version},
                )
            else:
                models = cached[1]

            feature_cols = [c for c in df.columns if c not in ["Open", "High", "Low", "Close", "Volume"]]
            if not feature_cols:
                return self._naive_predict(df)

            X = df[feature_cols].values
            latest = X[-1].reshape(1, -1)

            return {
                "1d":  float(models["1d"].predict(latest)[0]),
                "7d":  float(models["7d"].predict(latest)[0]),
                "30d": float(models["30d"].predict(latest)[0]),
            }
        except Exception as exc:
            logger.warning(f"XGBoost predict failed for {ticker}: {exc}", extra={"ticker": ticker})
            return self._naive_predict(df)

    # ── Prophet (use pre-computed forecast ratios from metadata) ─────────────

    def _prophet_predict(self, ticker: str, df: pd.DataFrame, current_price: float) -> dict:
        """
        Prophet is trained offline and stores forecast_ratios in metadata.json:
          { "forecast_ratios": {"1d": r1, "7d": r7, "30d": r30} }

        At inference we simply apply: predicted = current_price * ratio
        This is valid for up to 24h of model staleness (our retrain cadence).
        """
        try:
            meta = load_metadata("prophet", ticker)
            if not meta or "forecast_ratios" not in meta:
                return self._naive_predict(df)

            ratios = meta["forecast_ratios"]
            # Validate ratios are reasonable (between 0.5 and 1.5 = ±50% change)
            def safe_ratio(key: str) -> float:
                r = float(ratios.get(key, 1.0))
                return max(0.5, min(1.5, r))
            
            return {
                "1d":  current_price * safe_ratio("1d"),
                "7d":  current_price * safe_ratio("7d"),
                "30d": current_price * safe_ratio("30d"),
            }
        except Exception as exc:
            logger.warning(f"Prophet predict failed for {ticker}: {exc}", extra={"ticker": ticker})
            return self._naive_predict(df)

    # ── LSTM (load pretrained weights) ────────────────────────────────────────

    def _lstm_predict(self, ticker: str, featured_df: pd.DataFrame, current_price: float) -> dict:
        try:
            import torch

            meta = load_metadata("lstm", ticker)
            if not meta:
                return self._naive_predict(featured_df)

            version = meta["version"]
            features: list[str] = meta["features_used"]
            seq_len: int = meta.get("seq_len", SEQ_LEN)
            n_features: int = meta["n_features"]

            weights_path = model_file("lstm", ticker, ".pt")
            scaler_path  = model_file("lstm", ticker, "_scaler.pkl")
            if not weights_path.exists() or not scaler_path.exists():
                logger.warning(
                    f"LSTM artefacts missing for {ticker}",
                    extra={"ticker": ticker, "model_version": version},
                )
                return self._naive_predict(featured_df)

            scalers = joblib.load(scaler_path)
            scaler_X = scalers["scaler_X"]
            scaler_y = scalers["scaler_y"]
            saved_features: list[str] = scalers.get("features", features)

            # Align feature columns to what the model was trained on
            available = [c for c in saved_features if c in featured_df.columns]
            if len(available) < 4:
                return self._naive_predict(featured_df)

            if len(featured_df) < seq_len:
                return self._naive_predict(featured_df)

            feat_vals = featured_df[available].values[-seq_len:].astype(np.float32)
            feat_scaled = scaler_X.transform(feat_vals)

            model = build_lstm(len(available))
            state_dict = torch.load(weights_path, map_location="cpu", weights_only=True)
            model.load_state_dict(state_dict)
            model.eval()

            with torch.no_grad():
                x = torch.tensor(feat_scaled, dtype=torch.float32).unsqueeze(0)
                pred_scaled = model(x).item()

            pred_price = float(scaler_y.inverse_transform([[pred_scaled]])[0][0])

            # LSTM is trained for 7-day forward; extrapolate 1d / 30d using percentage change
            pct_change_7d = (pred_price - current_price) / current_price
            return {
                "1d":  current_price * (1 + pct_change_7d * (1 / 7)),
                "7d":  pred_price,
                "30d": current_price * (1 + pct_change_7d * (30 / 7)),
            }

        except Exception as exc:
            logger.warning(f"LSTM predict failed for {ticker}: {exc}", extra={"ticker": ticker})
            return self._naive_predict(featured_df)

    # ── Naive fallback ────────────────────────────────────────────────────────

    def _naive_predict(self, df: pd.DataFrame) -> dict:
        """30-day momentum extrapolation — last resort when all models absent."""
        close = df["Close"] if "Close" in df.columns else df.iloc[:, 0]
        current = float(close.iloc[-1])
        past_30 = float(close.iloc[-30]) if len(close) >= 30 else current
        daily_r = (current - past_30) / (past_30 * 30 + 1e-9)
        return {
            "1d":  current * (1 + daily_r),
            "7d":  current * (1 + daily_r * 7),
            "30d": current * (1 + daily_r * 30),
        }

    # ── Confidence ────────────────────────────────────────────────────────────

    def _compute_confidence(
        self,
        xgb: dict, prophet: dict, lstm: dict,
        technicals: dict,
        ticker: str,
    ) -> float:
        # Model agreement (50%)
        preds_7d = [xgb["7d"], prophet["7d"], lstm["7d"]]
        mean_p = abs(np.mean(preds_7d))
        std_p = np.std(preds_7d)
        agreement = 1.0 - min(std_p / (mean_p + 1e-9), 1.0)

        # MAPE-based (30%) — lower MAPE → higher confidence; cap at 10%
        mapes = []
        for mt in ("xgb", "lstm", "prophet"):
            meta = load_metadata(mt, ticker)
            if meta and "mape" in meta:
                mapes.append(float(meta["mape"]))
        mape_conf = 1.0 - min(np.mean(mapes) / 10.0, 1.0) if mapes else 0.5

        # Technical signal quality (20%)
        rsi = float(technicals.get("rsi") or 50)
        rsi_penalty = 0.15 if (rsi > 75 or rsi < 25) else 0.0
        tech_conf = 1.0 - rsi_penalty

        return max(0.0, min(1.0, 0.50 * agreement + 0.30 * mape_conf + 0.20 * tech_conf))

    # ── Risk ──────────────────────────────────────────────────────────────────

    def _compute_risk_score(self, df: pd.DataFrame, risk_profile: str) -> float:
        vol = df["volatility_20d"].iloc[-1] if "volatility_20d" in df.columns else 0.3
        raw = min(float(vol) * 20, 10.0)
        multiplier = RISK_MULTIPLIERS.get(risk_profile, 1.0)
        return round(raw * multiplier, 2)

    def _determine_signal(
        self,
        pred_7d: float,
        current: float,
        risk_score: float,
        risk_profile: str,
        regime: str,
    ) -> Signal:
        change_pct = (pred_7d - current) / current * 100
        threshold = _SIGNAL_THRESHOLDS.get(risk_profile, 2.0)

        # In bear regime, raise the buy bar and lower the sell bar
        if regime == "bear":
            threshold *= 1.5

        if change_pct > threshold and risk_score < 7:
            return Signal.BUY
        elif change_pct < -threshold:
            return Signal.SELL
        return Signal.HOLD

    def _risk_label(self, score: float) -> RiskLabel:
        if score < 3:
            return RiskLabel.LOW
        elif score < 5.5:
            return RiskLabel.MODERATE
        elif score < 7.5:
            return RiskLabel.HIGH
        return RiskLabel.VERY_HIGH

    # ── Factor explanation ────────────────────────────────────────────────────

    def _build_factors(
        self,
        ticker: str,
        featured_df: pd.DataFrame,
        technicals: dict,
        signal: Signal,
        pred_7d: float,
        current: float,
        sentiment_score: float,
        regime: str,
    ) -> list[str]:
        factors: list[str] = []
        pred_change = (pred_7d - current) / current * 100

        # 1. Price target
        direction = "+" if pred_change >= 0 else ""
        factors.append(f"7-day target: {direction}{pred_change:.1f}% (₹{pred_7d:,.2f})")

        # 2. XGBoost feature importances (top driver)
        factors += self._xgb_top_factors(ticker, featured_df, signal)

        # 3. Regime context
        regime_text = {"bull": "Bull market — upward bias", "bear": "Bear market — elevated caution", "sideways": "Sideways market — low momentum"}.get(regime, "")
        if regime_text:
            factors.append(regime_text)

        # 4. Sentiment
        if abs(sentiment_score) > 0.1:
            sent_dir = "Positive" if sentiment_score > 0 else "Negative"
            factors.append(f"{sent_dir} news sentiment ({sentiment_score:+.2f})")

        # 5. Technical fallbacks if fewer than 4 factors
        if len(factors) < 4:
            rsi = float(technicals.get("rsi") or 50)
            if rsi > 70:
                factors.append(f"RSI overbought at {rsi:.1f}")
            elif rsi < 30:
                factors.append(f"RSI oversold at {rsi:.1f}")
            macd_hist = float(technicals.get("macd_hist") or 0)
            if abs(macd_hist) > 0:
                factors.append(f"MACD histogram: {'positive' if macd_hist > 0 else 'negative'} ({macd_hist:.3f})")

        return factors[:5]

    def _xgb_top_factors(self, ticker: str, featured_df: pd.DataFrame, signal: Signal) -> list[str]:
        try:
            pkl = model_file("xgb", ticker, ".pkl")
            if not pkl.exists():
                return []
            cached = self._xgb_cache.get(ticker)
            models = cached[1] if cached else joblib.load(pkl)
            model_7d = models.get("7d")
            if model_7d is None:
                return []

            feature_cols = [c for c in featured_df.columns if c not in ["Open", "High", "Low", "Close", "Volume"]]
            importances = model_7d.feature_importances_
            top_idx = np.argsort(importances)[::-1][:2]
            results = []
            last_row = featured_df.iloc[-1]
            for idx in top_idx:
                if idx >= len(feature_cols):
                    continue
                fname = feature_cols[idx]
                val = float(last_row.get(fname, 0))
                label = _FEATURE_LABELS.get(fname, fname.replace("_", " ").title())
                results.append(f"{label}: {val:.3f}")
            return results
        except Exception:
            return []
