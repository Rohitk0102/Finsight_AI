"""
Prediction routes — Phase 2.

Rules enforced:
  • No model training here. All heavy work is precomputed by Celery.
  • FinBERT sentiment is read from Supabase ticker_sentiment (pre-computed nightly).
  • Sector correlation and volatility are computed on-the-fly but are fast (no fitting).
  • Predictions are persisted with predicted_price + current_price_at_pred for backtesting.
"""

from __future__ import annotations

import asyncio
import time
from typing import Optional

import httpx
import yfinance as yf
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from loguru import logger

from app.core.dependencies import get_current_user, rate_limit
from app.core.redis import redis_get, redis_set
from app.core.supabase import supabase
from app.ml.models.ensemble import EnsemblePredictor
from app.ml.signals.sector_correlation import compute_sector_correlation
from app.ml.signals.volatility import forecast_volatility
from app.schemas.stock import StockPrediction, PredictionAccuracy
from app.schemas.user import RiskProfile, InvestmentHorizon

router = APIRouter(prefix="/predict", tags=["predictions"])
predictor = EnsemblePredictor()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _request_ip(request: Optional[Request]) -> str:
    if request and request.client and request.client.host:
        return request.client.host
    return "unknown"


def _is_connectivity_error(exc: Exception) -> bool:
    if isinstance(exc, httpx.HTTPError):
        return True
    message = str(exc).lower()
    return any(
        marker in message
        for marker in (
            "nodename nor servname provided",
            "name or service not known",
            "temporary failure in name resolution",
            "connection refused",
            "timed out",
        )
    )


async def _apply_rate_limit(
    request: Optional[Request],
    endpoint: str,
    *,
    limit: int = 60,
    window: int = 60,
) -> None:
    try:
        await rate_limit(_request_ip(request), endpoint, limit=limit, window=window)
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning(f"Rate limit bypassed for {endpoint} due to Redis degradation: {exc}")


async def _execute_query(query, *, operation: str, fail_open: bool = False):
    try:
        return await asyncio.to_thread(query.execute)
    except Exception as exc:
        if fail_open:
            logger.warning(f"{operation} skipped due to DB degradation: {exc}")
            return None
        if _is_connectivity_error(exc):
            logger.error(f"{operation} failed due to DB connectivity: {exc}")
            raise HTTPException(
                status_code=503,
                detail="Database service unavailable. Check SUPABASE_URL/network and retry.",
            )
        logger.error(f"{operation} failed: {exc}")
        raise HTTPException(status_code=500, detail=f"{operation} failed")


async def _get_sentiment(ticker: str) -> float:
    """Read pre-computed sentiment from Supabase. Returns 0.0 if absent."""
    try:
        row = await _execute_query(
            supabase.table("ticker_sentiment")
            .select("sentiment_score")
            .eq("ticker", ticker)
            .maybe_single(),
            operation=f"sentiment_lookup:{ticker}",
            fail_open=True,
        )
        if row.data and row.data.get("sentiment_score") is not None:
            return float(row.data["sentiment_score"])
    except Exception as exc:
        logger.warning(f"Sentiment lookup failed for {ticker}: {exc}", extra={"ticker": ticker})
    return 0.0


# ── Prediction endpoint ───────────────────────────────────────────────────────

@router.get("/{ticker}", response_model=StockPrediction)
async def predict_stock(
    ticker: str,
    risk_profile: RiskProfile = Query(RiskProfile.MODERATE),
    horizon: InvestmentHorizon = Query(InvestmentHorizon.MEDIUM),
    request: Request = None,
    current_user: dict = Depends(get_current_user),
):
    """
    Ensemble ML prediction (XGBoost + Prophet + LSTM) with pre-computed
    FinBERT sentiment, market regime, sector correlation, and GARCH volatility.
    Cached 1 hour per ticker × risk_profile × horizon.
    """
    t0 = time.perf_counter()
    await _apply_rate_limit(request, "predict", limit=30, window=60)
    ticker = ticker.upper()

    cache_key = f"predict:v2:{ticker}:{risk_profile}:{horizon}"
    cached = await redis_get(cache_key)
    if cached:
        return cached

    # Read pre-computed sentiment (never infer inline)
    sentiment_score = await _get_sentiment(ticker)

    try:
        result: StockPrediction = await predictor.predict(
            ticker,
            risk_profile=risk_profile,
            horizon=horizon,
            sentiment_score=sentiment_score,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error(f"Prediction error for {ticker}: {exc}", extra={"ticker": ticker})
        raise HTTPException(status_code=500, detail="Prediction failed. Please try again.")

    # Sector correlation + GARCH volatility — run in thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    try:
        result.sector_correlation = await loop.run_in_executor(
            None, compute_sector_correlation, ticker
        )
    except Exception:
        result.sector_correlation = None
    try:
        hist = await loop.run_in_executor(
            None, lambda: yf.Ticker(ticker).history(period="1y", interval="1d")
        )
        result.volatility_forecast = await loop.run_in_executor(
            None, forecast_volatility, hist
        )
    except Exception:
        result.volatility_forecast = None

    await redis_set(cache_key, result.model_dump(), ttl=3600)

    latency_ms = round((time.perf_counter() - t0) * 1000, 1)
    logger.info(
        f"API predict complete",
        extra={
            "ticker": ticker,
            "model_version": result.model_version,
            "signal": result.signal,
            "latency_ms": latency_ms,
        },
    )

    # Persist prediction for backtesting resolution
    try:
        await _execute_query(
            supabase.table("predictions").insert({
                "user_id": current_user["id"],
                "ticker": ticker,
                "signal": result.signal,
                "confidence": result.confidence,
                "risk_score": result.risk_score,
                "predicted_7d": result.predicted_7d,
                "predicted_price": result.predicted_7d,
                "current_price_at_pred": result.current_price,
                "horizon_days": 7,
                "model_version": result.model_version,
                "risk_profile": risk_profile,
                "horizon": horizon,
            }),
            operation=f"prediction_persist:{ticker}",
            fail_open=True,
        )
    except Exception as exc:
        logger.warning(f"Prediction persistence failed for {ticker}: {exc}", extra={"ticker": ticker})

    return result


# ── Portfolio analysis ────────────────────────────────────────────────────────

@router.get("/portfolio/analysis")
async def analyze_portfolio(
    current_user: dict = Depends(get_current_user),
    request: Request = None,
):
    """Run predictions for all holdings in the user's portfolio."""
    await _apply_rate_limit(request, "portfolio_analysis", limit=5, window=60)

    holdings = await _execute_query(
        supabase.table("holdings")
        .select("ticker")
        .eq("user_id", current_user["id"]),
        operation="portfolio_holdings_fetch",
    )
    if not holdings.data:
        return {"message": "No holdings found", "analyses": []}

    profile = await _execute_query(
        supabase.table("user_profiles")
        .select("risk_profile, investment_horizon")
        .eq("clerk_id", current_user["id"])
        .maybe_single(),
        operation="portfolio_profile_fetch",
        fail_open=True,
    )
    risk    = profile.data.get("risk_profile", "moderate")    if profile.data else "moderate"
    horizon = profile.data.get("investment_horizon", "medium") if profile.data else "medium"

    tickers = list({h["ticker"] for h in holdings.data})
    results = []
    for ticker in tickers[:20]:
        try:
            sentiment_score = await _get_sentiment(ticker)
            pred = await predictor.predict(ticker, risk_profile=risk, horizon=horizon, sentiment_score=sentiment_score)
            results.append(pred.model_dump())
        except Exception as exc:
            logger.warning(f"Skipped {ticker} in portfolio analysis: {exc}", extra={"ticker": ticker})

    return {"analyses": results}


# ── Accuracy endpoints ────────────────────────────────────────────────────────

@router.get("/accuracy/{ticker}", response_model=list[PredictionAccuracy])
async def get_ticker_accuracy(
    ticker: str,
    horizon_days: Optional[int] = Query(None, description="Filter by horizon (1, 7, or 30)"),
    current_user: dict = Depends(get_current_user),
):
    """
    Return model accuracy metrics for *ticker*.
    Populated by the nightly backtest_resolver Celery task.
    """
    query = (
        supabase.table("model_accuracy")
        .select("*")
        .eq("ticker", ticker.upper())
        .order("computed_at", desc=True)
    )
    if horizon_days is not None:
        query = query.eq("horizon_days", horizon_days)

    result = await _execute_query(
        query.limit(10),
        operation=f"ticker_accuracy_fetch:{ticker.upper()}",
    )
    return result.data or []


@router.get("/accuracy/model/summary")
async def get_model_accuracy_summary(
    current_user: dict = Depends(get_current_user),
):
    """
    Aggregate accuracy across all tickers for the current model versions.
    Returns overall hit_rate and avg_mape per horizon.
    """
    rows = await _execute_query(
        supabase.table("model_accuracy")
        .select("horizon_days, hit_rate, avg_mape, n_samples")
        .not_.is_("hit_rate", "null"),
        operation="model_accuracy_summary_fetch",
    )
    if not rows.data:
        return {"horizons": {}}

    from collections import defaultdict
    import statistics

    buckets: dict[int, list] = defaultdict(list)
    for row in rows.data:
        h = int(row["horizon_days"])
        buckets[h].append(row)

    summary = {}
    for h, items in buckets.items():
        hit_rates = [r["hit_rate"] for r in items if r["hit_rate"] is not None]
        mapes     = [r["avg_mape"] for r in items if r["avg_mape"] is not None]
        total_n   = sum(r["n_samples"] for r in items)
        summary[str(h)] = {
            "horizon_days": h,
            "overall_hit_rate": round(statistics.mean(hit_rates), 4) if hit_rates else None,
            "overall_avg_mape": round(statistics.mean(mapes), 4)     if mapes     else None,
            "total_samples":    total_n,
            "ticker_count":     len(items),
        }

    return {"horizons": summary}


# ── Prediction history ────────────────────────────────────────────────────────

@router.get("/history/{ticker}")
async def get_prediction_history(
    ticker: str,
    limit: int = Query(30, le=100),
    current_user: dict = Depends(get_current_user),
):
    result = await _execute_query(
        supabase.table("predictions")
        .select("id, ticker, signal, confidence, predicted_price, current_price_at_pred, horizon_days, model_version, actual_price, direction_correct, mape, resolved_at, created_at")
        .eq("user_id", current_user["id"])
        .eq("ticker", ticker.upper())
        .order("created_at", desc=True)
        .limit(limit),
        operation=f"prediction_history_fetch:{ticker.upper()}",
    )
    return result.data
