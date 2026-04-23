"""
FinBERT sentiment pipeline — runs as a nightly Celery task.

Flow:
  1. Check ticker_sentiment.updated_at — skip if < 12h old.
  2. Fetch last 7 days of news from Finnhub.
  3. Run ProsusAI/finbert on each headline (batch inference).
  4. Aggregate: sentiment_score = mean(positive_score - negative_score).
  5. Upsert into ticker_sentiment table.

FinBERT output per text:
  [{"label": "positive", "score": 0.9}, {"label": "negative": 0.05}, ...]
  sentiment_score = positive_score - negative_score  ∈ [-1, +1]

Fallback: if transformers is not installed, uses VADER-style keyword scoring.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Optional
from loguru import logger

import httpx

from app.tasks.celery_app import celery_app
from app.tasks.data_sync import TRACKED_TICKERS
from app.core.supabase import supabase
from app.core.config import settings

# ── Keyword fallback ──────────────────────────────────────────────────────────

_POS = re.compile(
    r"\b(surges?|gains?|rises?|beats?|rallies?|profit|growth|strong|record|upgraded?|outperform)\b",
    re.I,
)
_NEG = re.compile(
    r"\b(falls?|drops?|slumps?|misses?|loss|decline|weak|downgrade|underperform|sells? off|crash)\b",
    re.I,
)


def _keyword_score(text: str) -> float:
    pos = len(_POS.findall(text))
    neg = len(_NEG.findall(text))
    total = pos + neg
    return (pos - neg) / total if total > 0 else 0.0


def _score_texts(headlines: list[str]) -> tuple[float, float]:
    """Returns (mean_score, mean_confidence) using Hugging Face API or keyword fallback."""
    if not headlines:
        return 0.0, 0.0

    import httpx
    import statistics

    scores, confs = [], []
    # yiyanghkust/finbert-tone is highly reliable on the serverless Inference API
    api_url = "https://api-inference.huggingface.co/models/yiyanghkust/finbert-tone"
    headers = {"Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"}

    # Use the API if token is present
    if settings.HUGGINGFACE_API_KEY:
        try:
            with httpx.Client(timeout=15) as client:
                # We send the headlines as inputs
                response = client.post(api_url, headers=headers, json={"inputs": headlines})
                response.raise_for_status()
                
                results = response.json()
                
                # Handling single string result vs list of results
                if isinstance(results, dict) and "error" in results:
                    raise Exception(f"HF API Error: {results['error']}")
                
                if not isinstance(results, list):
                    raise Exception("Unexpected HF API response format")

                # If single string passed, response is [ [ {...} ] ]
                # Since we passed a list, response is [ [ {...}, {...} ], ... ]
                for result in results:
                    # Convert labels to lowercase for robust matching
                    label_scores = {r["label"].lower(): r["score"] for r in result}
                    s = label_scores.get("positive", 0.0) - label_scores.get("negative", 0.0)
                    c = max(label_scores.values())
                    scores.append(s)
                    confs.append(c)

        except Exception as exc:
            logger.warning(f"FinBERT API inference failed: {exc}. Falling back to keyword scoring.")
            scores = []
            confs = []

    # Fallback to keyword scoring if API fails or no token
    if not scores:
        for h in headlines:
            scores.append(_keyword_score(h))
            confs.append(0.5)

    mean_score = statistics.mean(scores) if scores else 0.0
    mean_conf  = statistics.mean(confs)  if confs  else 0.0
    return round(float(mean_score), 4), round(float(mean_conf), 4)


# ── Freshness guard ───────────────────────────────────────────────────────────

def _sentiment_is_fresh(ticker: str, max_age_hours: float = 12.0) -> bool:
    try:
        row = (
            supabase.table("ticker_sentiment")
            .select("updated_at")
            .eq("ticker", ticker)
            .maybe_single()
            .execute()
        )
        if not row.data:
            return False
        updated_at = datetime.fromisoformat(row.data["updated_at"])
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)
        age_h = (datetime.now(timezone.utc) - updated_at).total_seconds() / 3600
        return age_h < max_age_hours
    except Exception:
        return False


# ── Celery tasks ──────────────────────────────────────────────────────────────

@celery_app.task(
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    name="app.tasks.sentiment_pipeline.compute_sentiment_for_ticker",
)
def compute_sentiment_for_ticker(self, ticker: str, force: bool = False) -> dict:
    """Compute FinBERT sentiment for *ticker* and upsert into ticker_sentiment."""
    if not force and _sentiment_is_fresh(ticker):
        logger.info(
            "Sentiment skipped (fresh)",
            extra={"ticker": ticker, "action": "skip_sentiment"},
        )
        return {"status": "skipped", "ticker": ticker}

    today = datetime.now(timezone.utc)
    from_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    to_date = today.strftime("%Y-%m-%d")

    headlines: list[str] = []
    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(
                "https://finnhub.io/api/v1/company-news",
                params={
                    "symbol": ticker.replace(".NS", "").replace(".BO", ""),
                    "from": from_date,
                    "to": to_date,
                    "token": settings.FINNHUB_API_KEY,
                },
            )
            items = resp.json() if isinstance(resp.json(), list) else []
            headlines = [item.get("headline", "") for item in items if item.get("headline")]
    except Exception as exc:
        logger.warning(f"Finnhub fetch failed for {ticker}: {exc}", extra={"ticker": ticker})

    if not headlines:
        # No news — store neutral score so caller has a row to read
        sentiment_score, confidence = 0.0, 0.0
        news_count = 0
    else:
        sentiment_score, confidence = _score_texts(headlines[:50])  # cap at 50 items
        news_count = len(headlines)

    supabase.table("ticker_sentiment").upsert(
        {
            "ticker": ticker,
            "sentiment_score": sentiment_score,
            "confidence": confidence,
            "news_count": news_count,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
        on_conflict="ticker",
    ).execute()

    logger.info(
        f"Sentiment computed: ticker={ticker} score={sentiment_score:.3f} n={news_count}",
        extra={"ticker": ticker, "sentiment_score": sentiment_score},
    )
    return {
        "status": "computed",
        "ticker": ticker,
        "sentiment_score": sentiment_score,
        "news_count": news_count,
    }


@celery_app.task(
    bind=True,
    max_retries=1,
    name="app.tasks.sentiment_pipeline.compute_sentiment_all",
)
def compute_sentiment_all(self) -> dict:
    """Fan out sentiment computation for all tracked tickers."""
    dispatched = 0
    for ticker in TRACKED_TICKERS:
        try:
            compute_sentiment_for_ticker.delay(ticker)
            dispatched += 1
        except Exception as exc:
            logger.error(f"Failed to dispatch sentiment for {ticker}: {exc}")
    logger.info(f"Sentiment pipeline dispatched for {dispatched} tickers")
    return {"dispatched": dispatched}
