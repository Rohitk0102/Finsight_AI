"""
Route-level tests for news endpoints with cache and rate-limit degradation handling.
"""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api.routes import news as news_routes
from app.schemas.news import MarketSentimentSummary, NewsArticle, NewsCategory, SentimentLabel
from app.services.news.news_service import NewsProvidersUnavailableError


def _request() -> SimpleNamespace:
    return SimpleNamespace(client=SimpleNamespace(host="127.0.0.1"))


def _article(
    article_id: str,
    title: str,
    *,
    ticker: str | None = None,
    category: NewsCategory = NewsCategory.GENERAL,
    sentiment: SentimentLabel = SentimentLabel.NEUTRAL,
    hours_ago: int = 1,
) -> NewsArticle:
    return NewsArticle(
        id=article_id,
        ticker=ticker,
        title=title,
        description="Sample description",
        url=f"https://example.com/{article_id}",
        source="Example",
        published_at=datetime.now(timezone.utc) - timedelta(hours=hours_ago),
        category=category,
        sentiment=sentiment,
        sentiment_score=0.0,
        sentiment_confidence=0.0,
    )


@pytest.mark.asyncio
async def test_market_news_uses_cache_hit(monkeypatch):
    cached = [
        {
            "id": "cached-1",
            "title": "Cached article",
            "description": "From cache",
            "summary": "From cache",
        }
    ]

    async def fake_rate_limit(*_args, **_kwargs):
        return None

    async def fake_cache_get(_key):
        return cached

    async def should_not_fetch(*_args, **_kwargs):
        raise AssertionError("Service should not be called on cache hit")

    monkeypatch.setattr(news_routes, "_apply_rate_limit", fake_rate_limit)
    monkeypatch.setattr(news_routes, "_cache_get", fake_cache_get)
    monkeypatch.setattr(news_routes.news_service, "get_market_news", should_not_fetch)

    result = await news_routes.get_market_news(limit=5, request=_request())
    assert result == cached


@pytest.mark.asyncio
async def test_market_news_degrades_when_redis_is_unavailable(monkeypatch):
    async def redis_down(*_args, **_kwargs):
        raise RuntimeError("redis unavailable")

    async def fetch_market_news(*_args, **_kwargs):
        return [_article("m1", "Markets hold steady")]

    monkeypatch.setattr(news_routes, "rate_limit", redis_down)
    monkeypatch.setattr(news_routes, "redis_get", redis_down)
    monkeypatch.setattr(news_routes, "redis_set", redis_down)
    monkeypatch.setattr(news_routes.news_service, "get_market_news", fetch_market_news)

    result = await news_routes.get_market_news(limit=5, request=_request())
    assert len(result) == 1
    assert result[0].title == "Markets hold steady"


@pytest.mark.asyncio
async def test_stock_news_writes_cache_with_compat_fields(monkeypatch):
    captured_cache = {}

    async def no_rate_limit(*_args, **_kwargs):
        return None

    async def cache_miss(*_args, **_kwargs):
        return None

    async def capture_cache(key, value, ttl=300):
        captured_cache["key"] = key
        captured_cache["value"] = value
        captured_cache["ttl"] = ttl

    async def fetch_stock_news(*_args, **_kwargs):
        return [_article("s1", "INFY announces major deal")]

    monkeypatch.setattr(news_routes, "rate_limit", no_rate_limit)
    monkeypatch.setattr(news_routes, "redis_get", cache_miss)
    monkeypatch.setattr(news_routes, "redis_set", capture_cache)
    monkeypatch.setattr(news_routes.news_service, "get_stock_news", fetch_stock_news)

    result = await news_routes.get_stock_news("infy", limit=2, request=_request())
    assert len(result) == 1
    assert captured_cache["ttl"] == 300
    assert captured_cache["key"] == "news:INFY:2"
    assert captured_cache["value"][0]["description"] == "Sample description"
    assert captured_cache["value"][0]["summary"] == "Sample description"
    assert isinstance(captured_cache["value"][0]["published_at"], str)


@pytest.mark.asyncio
async def test_sentiment_route_degrades_when_redis_is_unavailable(monkeypatch):
    async def redis_down(*_args, **_kwargs):
        raise RuntimeError("redis unavailable")

    async def fake_summary(*_args, **_kwargs):
        return MarketSentimentSummary(
            ticker="AAPL",
            overall_sentiment=SentimentLabel.NEUTRAL,
            sentiment_score=0.0,
            article_count=0,
            positive_count=0,
            negative_count=0,
            neutral_count=0,
            computed_at=datetime.now(timezone.utc),
        )

    monkeypatch.setattr(news_routes, "rate_limit", redis_down)
    monkeypatch.setattr(news_routes, "redis_get", redis_down)
    monkeypatch.setattr(news_routes, "redis_set", redis_down)
    monkeypatch.setattr(news_routes.news_service, "get_sentiment_summary", fake_summary)

    result = await news_routes.get_sentiment("aapl", request=_request())
    assert result.ticker == "AAPL"
    assert result.overall_sentiment == SentimentLabel.NEUTRAL


@pytest.mark.asyncio
async def test_list_news_filters_and_paginates(monkeypatch):
    async def no_rate_limit(*_args, **_kwargs):
        return None

    async def cache_miss(*_args, **_kwargs):
        return None

    captured_cache = {}

    async def capture_cache(key, value, ttl=300):
        captured_cache["key"] = key
        captured_cache["value"] = value
        captured_cache["ttl"] = ttl

    async def fetch_market_news(*_args, **_kwargs):
        return [
            _article("n1", "Older neutral", category=NewsCategory.GENERAL, sentiment=SentimentLabel.NEUTRAL, hours_ago=80),
            _article("n2", "Recent positive earnings", category=NewsCategory.EARNINGS, sentiment=SentimentLabel.POSITIVE, hours_ago=2),
            _article("n3", "Recent positive merger", category=NewsCategory.MERGER, sentiment=SentimentLabel.POSITIVE, hours_ago=3),
            _article("n4", "Recent negative earnings", category=NewsCategory.EARNINGS, sentiment=SentimentLabel.NEGATIVE, hours_ago=1),
        ]

    monkeypatch.setattr(news_routes, "rate_limit", no_rate_limit)
    monkeypatch.setattr(news_routes, "redis_get", cache_miss)
    monkeypatch.setattr(news_routes, "redis_set", capture_cache)
    monkeypatch.setattr(news_routes.news_service, "get_market_news", fetch_market_news)

    result = await news_routes.list_news(
        page=1,
        limit=1,
        category="earnings",
        sentiment="positive",
        time_range="24h",
        request=_request(),
    )

    assert result.total == 1
    assert result.has_more is False
    assert len(result.articles) == 1
    assert result.articles[0].id == "n2"
    assert captured_cache["ttl"] == 300
    assert captured_cache["value"]["articles"][0]["id"] == "n2"


@pytest.mark.asyncio
async def test_list_news_uses_ticker_source(monkeypatch):
    async def no_rate_limit(*_args, **_kwargs):
        return None

    async def cache_miss(*_args, **_kwargs):
        return None

    async def no_cache_set(*_args, **_kwargs):
        return None

    called = {"ticker": None}

    async def fetch_stock_news(ticker: str, limit: int):
        called["ticker"] = ticker
        assert limit >= 100
        return [_article("s1", "Ticker scoped", ticker=ticker)]

    monkeypatch.setattr(news_routes, "rate_limit", no_rate_limit)
    monkeypatch.setattr(news_routes, "redis_get", cache_miss)
    monkeypatch.setattr(news_routes, "redis_set", no_cache_set)
    monkeypatch.setattr(news_routes.news_service, "get_stock_news", fetch_stock_news)

    result = await news_routes.list_news(
        page=1,
        limit=20,
        ticker="infy",
        request=_request(),
    )
    assert called["ticker"] == "INFY"
    assert result.total == 1
    assert result.articles[0].ticker == "INFY"


@pytest.mark.asyncio
async def test_market_news_returns_503_when_providers_are_unavailable(monkeypatch):
    async def no_rate_limit(*_args, **_kwargs):
        return None

    async def cache_miss(*_args, **_kwargs):
        return None

    async def unavailable(*_args, **_kwargs):
        raise NewsProvidersUnavailableError("News providers are temporarily unavailable.")

    monkeypatch.setattr(news_routes, "_apply_rate_limit", no_rate_limit)
    monkeypatch.setattr(news_routes, "_cache_get", cache_miss)
    monkeypatch.setattr(news_routes.news_service, "get_market_news", unavailable)

    with pytest.raises(HTTPException) as exc_info:
        await news_routes.get_market_news(limit=5, request=_request())

    assert exc_info.value.status_code == 503
    assert "temporarily unavailable" in exc_info.value.detail


@pytest.mark.asyncio
async def test_list_news_does_not_cache_empty_payload(monkeypatch):
    async def no_rate_limit(*_args, **_kwargs):
        return None

    async def cache_miss(*_args, **_kwargs):
        return None

    cached = {"called": False}

    async def capture_cache(*_args, **_kwargs):
        cached["called"] = True

    async def fetch_market_news(*_args, **_kwargs):
        return []

    monkeypatch.setattr(news_routes, "_apply_rate_limit", no_rate_limit)
    monkeypatch.setattr(news_routes, "_cache_get", cache_miss)
    monkeypatch.setattr(news_routes, "_cache_set", capture_cache)
    monkeypatch.setattr(news_routes.news_service, "get_market_news", fetch_market_news)

    result = await news_routes.list_news(page=1, limit=20, request=_request())

    assert result.total == 0
    assert result.articles == []
    assert cached["called"] is False
