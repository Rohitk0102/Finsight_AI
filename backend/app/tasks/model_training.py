"""
Celery tasks for training all three ML models (XGBoost, Prophet, LSTM).

Design rules:
  - Each task is idempotent: skips if model was trained within last 24h.
  - autoretry_for on transient network errors; retry_backoff=True.
  - No EnsemblePredictor.predict() calls — training is fully separate.
  - XGBoost and Prophet training results store forecast_ratios in metadata.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import yfinance as yf
import joblib
from datetime import datetime, timezone
from pathlib import Path
from loguru import logger

from app.tasks.celery_app import celery_app
from app.tasks.data_sync import TRACKED_TICKERS
from app.ml.models.model_store import (
    _ticker_dir,
    save_metadata,
    next_version_tag,
    needs_training,
    load_metadata,
)
from app.ml.utils.feature_engineering import compute_features


# ── XGBoost ───────────────────────────────────────────────────────────────────

@celery_app.task(
    bind=True,
    max_retries=2,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=120,
    name="app.tasks.model_training.train_xgboost",
)
def train_xgboost(self, ticker: str, force: bool = False) -> dict:
    """Train / refresh XGBoost model for *ticker*."""
    if not force and not needs_training("xgb", ticker):
        logger.info("XGBoost skipped (fresh)", extra={"ticker": ticker, "action": "skip_train"})
        return {"status": "skipped", "ticker": ticker}

    try:
        from xgboost import XGBRegressor
    except ImportError:
        raise RuntimeError("xgboost is not installed")

    t = yf.Ticker(ticker)
    df = t.history(period="2y", interval="1d")
    df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
    if len(df) < 80:
        raise ValueError(f"Insufficient data for {ticker}: {len(df)} rows")

    featured = compute_features(df)
    feature_cols = [c for c in featured.columns if c not in ["Open", "High", "Low", "Close", "Volume"]]
    if len(feature_cols) < 5:
        raise ValueError(f"Too few features for {ticker}")

    X = featured[feature_cols].values
    current_price = float(df["Close"].iloc[-1])

    targets = {
        "1d":  featured["Close"].shift(-1).fillna(featured["Close"]).values,
        "7d":  featured["Close"].shift(-7).fillna(featured["Close"]).values,
        "30d": featured["Close"].shift(-30).fillna(featured["Close"]).values,
    }

    models: dict[str, XGBRegressor] = {}
    mapes: list[float] = []

    for label, y in targets.items():
        train_end = len(X) - 30
        m = XGBRegressor(
            n_estimators=300,
            max_depth=4,
            learning_rate=0.03,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_weight=3,
            gamma=0.1,
            reg_alpha=0.1,
            reg_lambda=1.0,
            random_state=42,
            n_jobs=-1,
        )
        m.fit(
            X[:train_end], y[:train_end],
            eval_set=[(X[train_end:], y[train_end:])],
            verbose=False,
        )
        models[label] = m

        # Val MAPE
        val_pred = m.predict(X[train_end:])
        val_true = y[train_end:]
        mape = float(np.mean(np.abs((val_true - val_pred) / (np.abs(val_true) + 1e-9))) * 100)
        mapes.append(mape)

    # Pre-compute forecast ratios from current feature vector
    latest = X[-1].reshape(1, -1)
    forecast_ratios = {
        label: float(models[label].predict(latest)[0]) / current_price
        for label in ("1d", "7d", "30d")
    }

    version = next_version_tag("xgb", ticker)
    d = _ticker_dir("xgb", ticker)
    joblib.dump(models, d / f"{version}.pkl")

    meta = {
        "version": version,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "features_used": feature_cols,
        "mape": round(float(np.mean(mapes)), 4),
        "n_samples": len(X),
        "forecast_ratios": forecast_ratios,
    }
    save_metadata("xgb", ticker, meta)
    logger.info(
        f"XGBoost trained: ticker={ticker} version={version} mape={meta['mape']:.2f}%",
        extra={"ticker": ticker, "model_version": version},
    )
    return {"status": "trained", "ticker": ticker, "version": version, "mape": meta["mape"]}


# ── Prophet ───────────────────────────────────────────────────────────────────

@celery_app.task(
    bind=True,
    max_retries=2,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=120,
    name="app.tasks.model_training.train_prophet",
)
def train_prophet(self, ticker: str, force: bool = False) -> dict:
    """
    Fit Prophet on 2y of daily closes, save the model and forecast_ratios.
    forecast_ratios = {1d: ratio, 7d: ratio, 30d: ratio}
    Ratios are applied to the live current_price at inference time.
    """
    if not force and not needs_training("prophet", ticker):
        logger.info("Prophet skipped (fresh)", extra={"ticker": ticker, "action": "skip_train"})
        return {"status": "skipped", "ticker": ticker}

    try:
        from prophet import Prophet
    except ImportError:
        logger.warning("prophet not installed, skipping", extra={"ticker": ticker})
        return {"status": "skipped", "ticker": ticker, "reason": "prophet not installed"}

    t = yf.Ticker(ticker)
    df = t.history(period="2y", interval="1d")
    df = df[["Close"]].dropna()
    if len(df) < 80:
        raise ValueError(f"Insufficient data for {ticker}")

    prophet_df = (
        df.reset_index()[["Date", "Close"]]
        .rename(columns={"Date": "ds", "Close": "y"})
    )
    prophet_df["ds"] = pd.to_datetime(prophet_df["ds"]).dt.tz_localize(None)

    m = Prophet(
        daily_seasonality=False,
        weekly_seasonality=True,
        yearly_seasonality=True,
        changepoint_prior_scale=0.05,
        seasonality_mode="multiplicative",
    )
    m.fit(prophet_df)

    future = m.make_future_dataframe(periods=30, freq="D")
    forecast = m.predict(future)

    last_close = float(df["Close"].iloc[-1])
    last_date = prophet_df["ds"].max()
    future_fc = forecast[forecast["ds"] > last_date].reset_index(drop=True)

    def _ratio(n_days: int) -> float:
        if future_fc.empty:
            return 1.0
        target = last_date + pd.Timedelta(days=n_days)
        idx = (future_fc["ds"] - target).abs().idxmin()
        predicted = float(future_fc.loc[idx, "yhat"])
        ratio = predicted / (last_close + 1e-9)
        # Clamp ratio to reasonable bounds (±50% change max)
        return max(0.5, min(1.5, ratio))

    # Val MAPE on held-out last 30 days
    train_df = prophet_df.iloc[:-30]
    val_df   = prophet_df.iloc[-30:]
    m_val = Prophet(
        daily_seasonality=False, weekly_seasonality=True, yearly_seasonality=True,
        changepoint_prior_scale=0.05, seasonality_mode="multiplicative",
    )
    m_val.fit(train_df)
    fc_val = m_val.predict(m_val.make_future_dataframe(periods=30, freq="D"))
    fc_val = fc_val[fc_val["ds"].isin(val_df["ds"])].reset_index(drop=True)
    if not fc_val.empty:
        pred_prices = fc_val["yhat"].values
        true_prices = val_df["y"].values[:len(pred_prices)]
        mape = float(np.mean(np.abs((true_prices - pred_prices) / (np.abs(true_prices) + 1e-9))) * 100)
    else:
        mape = 999.0

    forecast_ratios = {"1d": round(_ratio(1), 6), "7d": round(_ratio(7), 6), "30d": round(_ratio(30), 6)}

    version = next_version_tag("prophet", ticker)
    d = _ticker_dir("prophet", ticker)
    joblib.dump(m, d / f"{version}.pkl")

    meta = {
        "version": version,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "features_used": ["Close"],
        "mape": round(mape, 4),
        "n_samples": len(df),
        "forecast_ratios": forecast_ratios,
        "last_close": last_close,
    }
    save_metadata("prophet", ticker, meta)
    logger.info(
        f"Prophet trained: ticker={ticker} version={version} mape={mape:.2f}%",
        extra={"ticker": ticker, "model_version": version},
    )
    return {"status": "trained", "ticker": ticker, "version": version, "mape": mape}


# ── LSTM ──────────────────────────────────────────────────────────────────────

@celery_app.task(
    bind=True,
    max_retries=2,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=180,
    name="app.tasks.model_training.train_lstm_task",
)
def train_lstm_task(self, ticker: str, force: bool = False) -> dict:
    """Celery wrapper around lstm_trainer.train_lstm."""
    from app.ml.models.lstm_trainer import train_lstm

    result = train_lstm(ticker, force=force)
    if result is None:
        return {"status": "skipped", "ticker": ticker}
    return {"status": "trained", "ticker": ticker, "version": result["version"], "mape": result["mape"]}


# ── Bulk retrain ──────────────────────────────────────────────────────────────

@celery_app.task(
    bind=True,
    max_retries=1,
    name="app.tasks.model_training.retrain_all",
)
def retrain_all(self) -> dict:
    """Fan out training tasks for all tracked tickers."""
    success, failed = 0, 0
    for ticker in TRACKED_TICKERS:
        try:
            train_xgboost.delay(ticker)
            train_prophet.delay(ticker)
            train_lstm_task.delay(ticker)
            success += 1
        except Exception as exc:
            logger.error(f"Failed to enqueue training for {ticker}: {exc}")
            failed += 1
    logger.info(f"retrain_all dispatched: {success} tickers, {failed} failed")
    return {"dispatched": success, "failed": failed}
