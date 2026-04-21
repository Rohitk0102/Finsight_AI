from datetime import datetime, timedelta, timezone
from typing import Optional
import traceback

from fastapi import APIRouter, Query, Request, HTTPException
from app.schemas.news import (
    NewsArticle,
    MarketSentimentSummary,
    NewsListResponse,
    NewsCategory,
    SentimentLabel,
)
from app.core.dependencies import rate_limit
from app.core.redis import redis_get, redis_set
from app.services.news.news_service import NewsProvidersUnavailableError, NewsService
from loguru import logger

router = APIRouter(prefix="/news", tags=["news"])
news_service = NewsService()


def _request_ip(request: Optional[Request]) -> str:
    if request and request.client and request.client.host:
        return request.client.host
    return "unknown"


async def _apply_rate_limit(ip: str, endpoint: str) -> None:
    try:
        await rate_limit(ip, endpoint)
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning(f"Rate limit bypassed for {endpoint} due to Redis degradation: {exc}")


async def _cache_get(cache_key: str):
    try:
        return await redis_get(cache_key)
    except Exception as exc:
        logger.warning(f"Cache get bypassed for {cache_key}: {exc}")
        return None


async def _cache_set(cache_key: str, value, ttl: int) -> None:
    try:
        await redis_set(cache_key, value, ttl=ttl)
    except Exception as exc:
        logger.warning(f"Cache set skipped for {cache_key}: {exc}")


def _news_service_unavailable(exc: NewsProvidersUnavailableError) -> HTTPException:
    return HTTPException(status_code=503, detail=str(exc))


def _parse_category(category: Optional[str]) -> Optional[NewsCategory]:
    if not category:
        return None
    try:
        return NewsCategory(category)
    except ValueError:
        return None


def _parse_sentiment(sentiment: Optional[str]) -> Optional[SentimentLabel]:
    if not sentiment:
        return None
    try:
        return SentimentLabel(sentiment)
    except ValueError:
        return None


def _parse_time_range(time_range: Optional[str]) -> Optional[timedelta]:
    if not time_range:
        return None
    mapping = {
        "1h": timedelta(hours=1),
        "6h": timedelta(hours=6),
        "24h": timedelta(hours=24),
        "7d": timedelta(days=7),
        "30d": timedelta(days=30),
    }
    return mapping.get(time_range)


@router.get("", response_model=NewsListResponse)
async def list_news(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    ticker: Optional[str] = None,
    category: Optional[str] = None,
    sentiment: Optional[str] = None,
    time_range: Optional[str] = Query(None, pattern=r"^(1h|6h|24h|7d|30d)$"),
    request: Request = None,
):
    """List paginated news with optional filters."""
    await _apply_rate_limit(_request_ip(request), "news_list")
    normalized_ticker = ticker.upper().strip() if ticker else None
    cache_key = f"news:list:{page}:{limit}:{normalized_ticker}:{category}:{sentiment}:{time_range}"
    cached = await _cache_get(cache_key)
    if cached:
        return cached

    fetch_limit = max(100, limit * page * 3)
    try:
        if normalized_ticker:
            articles = await news_service.get_stock_news(normalized_ticker, limit=fetch_limit)
        else:
            articles = await news_service.get_market_news(limit=fetch_limit, category=category)
    except NewsProvidersUnavailableError as exc:
        raise _news_service_unavailable(exc) from exc

    category_filter = _parse_category(category)
    sentiment_filter = _parse_sentiment(sentiment)
    time_delta = _parse_time_range(time_range)

    if category_filter:
        articles = [a for a in articles if a.category == category_filter]
    if sentiment_filter:
        articles = [a for a in articles if a.sentiment == sentiment_filter]
    if time_delta:
        cutoff = datetime.now(timezone.utc) - time_delta
        articles = [
            a for a in articles
            if (a.published_at if a.published_at.tzinfo is not None else a.published_at.replace(tzinfo=timezone.utc)) >= cutoff
        ]

    total = len(articles)
    start = (page - 1) * limit
    end = start + limit
    page_articles = articles[start:end]

    payload = NewsListResponse(
        articles=page_articles,
        total=total,
        page=page,
        limit=limit,
        has_more=end < total,
    )
    if payload.articles:
        await _cache_set(cache_key, payload.model_dump(mode="json"), ttl=300)
    return payload


@router.get("/market", response_model=list[NewsArticle])
async def get_market_news(
    limit: int = Query(20, le=50),
    category: Optional[str] = None,
    request: Request = None,
):
    """Latest market-wide news."""
    await _apply_rate_limit(_request_ip(request), "news_market")
    cache_key = f"news:market:{category}:{limit}"
    cached = await _cache_get(cache_key)
    if cached:
        return cached

    try:
        articles = await news_service.get_market_news(limit=limit, category=category)
    except NewsProvidersUnavailableError as exc:
        raise _news_service_unavailable(exc) from exc

    if articles:
        await _cache_set(cache_key, [a.model_dump(mode="json") for a in articles], ttl=300)
    return articles


@router.get("/{ticker}", response_model=list[NewsArticle])
async def get_stock_news(
    ticker: str,
    limit: int = Query(10, le=30),
    request: Request = None,
):
    """News for a specific stock ticker."""
    await _apply_rate_limit(_request_ip(request), "news_ticker")
    ticker = ticker.upper()
    cache_key = f"news:{ticker}:{limit}"
    cached = await _cache_get(cache_key)
    if cached:
        return cached

    try:
        articles = await news_service.get_stock_news(ticker, limit=limit)
    except NewsProvidersUnavailableError as exc:
        raise _news_service_unavailable(exc) from exc

    if articles:
        await _cache_set(cache_key, [a.model_dump(mode="json") for a in articles], ttl=300)
    return articles


@router.get("/sentiment/{ticker}", response_model=MarketSentimentSummary)
async def get_sentiment(ticker: str, request: Request):
    """Aggregate sentiment score for a ticker (last 24h)."""
    await _apply_rate_limit(_request_ip(request), "sentiment")
    ticker = ticker.upper()
    cache_key = f"sentiment:{ticker}"
    cached = await _cache_get(cache_key)
    if cached:
        return cached

    summary = await news_service.get_sentiment_summary(ticker)
    await _cache_set(cache_key, summary.model_dump(mode="json"), ttl=1800)
    return summary
