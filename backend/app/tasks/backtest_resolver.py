"""
Backtesting resolver — runs daily, resolves unresolved predictions.

Algorithm:
  1. Query predictions WHERE resolved_at IS NULL AND
       created_at + horizon_days < NOW()  (prediction horizon has passed).
  2. For each row, fetch the actual closing price on the first trading day
     >= (created_at + horizon_days). Uses yfinance history for robustness
     against non-trading days.
  3. Compute:
       direction_correct = sign(actual - prev_close) == sign(predicted - prev_close)
       mape              = |actual - predicted| / |actual| * 100
  4. Update the predictions row.
  5. Refresh model_accuracy aggregate table.

Guard: already-resolved predictions are never touched (resolved_at IS NOT NULL).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta, timezone
from loguru import logger

from app.tasks.celery_app import celery_app
from app.core.supabase import supabase


# ── Actual price fetching ─────────────────────────────────────────────────────

def _fetch_actual_price(ticker: str, target_date: datetime) -> tuple[float | None, datetime | None]:
    """
    Return (close_price, actual_date) for the first available trading day
    on or after *target_date*. Tries up to 10 calendar days forward to
    skip weekends / public holidays.
    """
    start = target_date.date()
    end = (target_date + timedelta(days=14)).date()
    try:
        t = yf.Ticker(ticker)
        hist = t.history(start=str(start), end=str(end), interval="1d")
        if hist.empty:
            return None, None
        first_row = hist.iloc[0]
        actual_price = float(first_row["Close"])
        actual_date = hist.index[0]
        if hasattr(actual_date, "to_pydatetime"):
            actual_date = actual_date.to_pydatetime()
        if actual_date.tzinfo is None:
            actual_date = actual_date.replace(tzinfo=timezone.utc)
        return actual_price, actual_date
    except Exception as exc:
        logger.warning(f"Price fetch failed for {ticker} on {start}: {exc}", extra={"ticker": ticker})
        return None, None


def _direction_correct(predicted: float, actual: float, prev_close: float) -> bool:
    """True if predicted and actual price moved in the same direction vs prev_close."""
    return float(np.sign(predicted - prev_close)) == float(np.sign(actual - prev_close))


def _mape(predicted: float, actual: float) -> float:
    return abs(actual - predicted) / (abs(actual) + 1e-9) * 100


# ── Celery tasks ──────────────────────────────────────────────────────────────

@celery_app.task(
    bind=True,
    max_retries=2,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    name="app.tasks.backtest_resolver.resolve_predictions",
)
def resolve_predictions(self) -> dict:
    """
    Resolve all mature unresolved predictions and refresh accuracy aggregates.
    """
    now = datetime.now(timezone.utc)
    resolved_count = 0
    failed_count = 0

    # ── Fetch unresolved rows whose horizon has elapsed ───────────────────────
    rows = (
        supabase.table("predictions")
        .select("id, ticker, predicted_price, current_price_at_pred, horizon_days, created_at, model_version")
        .is_("resolved_at", "null")
        .not_.is_("predicted_price", "null")
        .execute()
    )

    for row in (rows.data or []):
        try:
            created_at = datetime.fromisoformat(row["created_at"])
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)

            horizon_days: int = int(row.get("horizon_days") or 7)
            maturity = created_at + timedelta(days=horizon_days)

            if maturity > now:
                continue  # not yet mature

            ticker = row["ticker"]
            predicted_price = float(row["predicted_price"])
            prev_close = float(row.get("current_price_at_pred") or predicted_price)

            actual_price, actual_date = _fetch_actual_price(ticker, maturity)
            if actual_price is None:
                logger.warning(
                    f"Could not fetch actual price for {ticker} prediction {row['id']}",
                    extra={"ticker": ticker},
                )
                failed_count += 1
                continue

            dir_correct = _direction_correct(predicted_price, actual_price, prev_close)
            mape_val = round(_mape(predicted_price, actual_price), 4)

            supabase.table("predictions").update({
                "actual_price": actual_price,
                "direction_correct": dir_correct,
                "mape": mape_val,
                "resolved_at": now.isoformat(),
            }).eq("id", row["id"]).execute()

            resolved_count += 1

        except Exception as exc:
            logger.error(
                f"Failed to resolve prediction {row.get('id')}: {exc}",
                extra={"ticker": row.get("ticker", "")},
            )
            failed_count += 1

    logger.info(
        f"resolve_predictions complete: resolved={resolved_count} failed={failed_count}",
        extra={"resolved": resolved_count, "failed": failed_count},
    )

    # Refresh accuracy aggregates for affected tickers
    if resolved_count > 0:
        _refresh_accuracy_aggregates()

    return {"resolved": resolved_count, "failed": failed_count}


def _refresh_accuracy_aggregates() -> None:
    """
    Recompute model_accuracy table from all resolved predictions.
    Groups by (ticker, horizon_days, model_version).
    """
    try:
        rows = (
            supabase.table("predictions")
            .select("ticker, horizon_days, model_version, direction_correct, mape")
            .not_.is_("resolved_at", "null")
            .not_.is_("mape", "null")
            .execute()
        )
        if not rows.data:
            return

        df = pd.DataFrame(rows.data)
        groups = df.groupby(["ticker", "horizon_days", "model_version"])

        upsert_rows = []
        for (ticker, horizon_days, model_version), grp in groups:
            hit_rate = float(grp["direction_correct"].mean()) if "direction_correct" in grp.columns else None
            avg_mape = float(grp["mape"].mean()) if "mape" in grp.columns else None
            upsert_rows.append({
                "ticker": ticker,
                "horizon_days": int(horizon_days),
                "model_version": str(model_version) if model_version else "unknown",
                "hit_rate": round(hit_rate, 4) if hit_rate is not None else None,
                "avg_mape": round(avg_mape, 4) if avg_mape is not None else None,
                "n_samples": len(grp),
                "computed_at": datetime.now(timezone.utc).isoformat(),
            })

        if upsert_rows:
            supabase.table("model_accuracy").upsert(
                upsert_rows,
                on_conflict="ticker,horizon_days,model_version",
            ).execute()
            logger.info(f"model_accuracy refreshed: {len(upsert_rows)} rows")

    except Exception as exc:
        logger.error(f"Accuracy aggregate refresh failed: {exc}")
