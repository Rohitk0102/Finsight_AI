"""
Regression tests for news service schema compatibility and aggregation behavior.
"""
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.news import NewsArticle, NewsCategory, SentimentLabel
from app.services.news.aggregator import AggregationResult
from app.services.news.news_service import NewsProvidersUnavailableError, NewsService


def _build_article(
    article_id: str,
    title: str,
    description: str,
    *,
    published_at: datetime | None = None,
    ticker: str | None = None,
    category: NewsCategory = NewsCategory.GENERAL,
) -> NewsArticle:
    return NewsArticle(
        id=article_id,
        ticker=ticker,
        title=title,
        description=description,
        url=f"https://example.com/{article_id}",
        source="TestSource",
        published_at=published_at or datetime.now(timezone.utc),
        category=category,
        sentiment=SentimentLabel.NEUTRAL,
        sentiment_score=0.0,
        sentiment_confidence=0.0,
    )


@pytest.mark.asyncio
async def test_get_market_news_returns_schema_compatible_articles(monkeypatch):
    service = NewsService()

    async def fake_aggregate(query: str, limit: int):
        assert query == "stock market india"
        assert limit >= 12
        return AggregationResult(
            articles=[
                _build_article("1", "Markets surge on earnings", "Benchmarks rallied today."),
                _build_article("2", "Markets surge on earnings", "Duplicate title should collapse."),
                _build_article("3", "Inflation concerns rise", "Macro pressure remains elevated."),
            ],
            attempted_sources=("newsapi", "gnews"),
            successful_sources=("newsapi", "gnews"),
            empty_sources=(),
            failed_sources=(),
            skipped_sources=(),
        )

    monkeypatch.setattr(service.aggregator, "aggregate_market_sources", fake_aggregate)
    articles = await service.get_market_news(limit=4)

    assert len(articles) == 2
    assert all(a.ticker is None for a in articles)
    assert all(0.0 <= a.sentiment_confidence <= 1.0 for a in articles)

    payload = articles[0].model_dump()
    assert "description" in payload
    assert "summary" in payload
    assert payload["summary"] == payload["description"]


@pytest.mark.asyncio
async def test_get_stock_news_sets_ticker_and_related_tickers(monkeypatch):
    service = NewsService()

    async def fake_aggregate(query: str, limit: int):
        assert query == "RELIANCE"
        assert limit >= 6
        return AggregationResult(
            articles=[
                _build_article(
                    "1",
                    "Reliance beats Q4 estimates",
                    "Profit growth exceeded analyst expectations.",
                    ticker=None,
                    category=NewsCategory.EARNINGS,
                )
            ],
            attempted_sources=("newsapi", "gnews", "finnhub"),
            successful_sources=("newsapi",),
            empty_sources=("gnews",),
            failed_sources=(),
            skipped_sources=("alpha_vantage", "marketaux"),
        )

    monkeypatch.setattr(service.aggregator, "aggregate_ticker_sources", fake_aggregate)
    articles = await service.get_stock_news("reliance", limit=2)

    assert len(articles) == 1
    assert articles[0].ticker == "RELIANCE"
    assert "RELIANCE" in articles[0].related_tickers

    payload = articles[0].model_dump()
    assert payload["description"] == "Profit growth exceeded analyst expectations."
    assert payload["summary"] == payload["description"]


def test_news_article_requires_description_field():
    with pytest.raises(ValidationError) as exc:
        NewsArticle(
            id="missing-description",
            title="Bad payload",
            summary="legacy field only",
            url="https://example.com/bad",
            source="Example",
            published_at=datetime.now(timezone.utc),
            sentiment=SentimentLabel.NEUTRAL,
            sentiment_score=0.0,
            sentiment_confidence=0.0,
            category=NewsCategory.GENERAL,
        )

    errors = exc.value.errors()
    assert any(err["loc"] == ("description",) and err["type"] == "missing" for err in errors)

    article = NewsArticle(
        id="ok",
        title="Valid payload",
        description="Uses canonical field.",
        url="https://example.com/ok",
        source="Example",
        published_at=datetime.now(timezone.utc),
        sentiment=SentimentLabel.NEUTRAL,
        sentiment_score=0.0,
        sentiment_confidence=0.0,
        category=NewsCategory.GENERAL,
    )
    assert article.summary == "Uses canonical field."


@pytest.mark.asyncio
async def test_get_market_news_raises_when_providers_fail_without_articles(monkeypatch):
    service = NewsService()

    async def fake_aggregate(query: str, limit: int):
        assert query == "stock market india"
        assert limit >= 12
        return AggregationResult(
            articles=[],
            attempted_sources=("newsapi", "gnews"),
            successful_sources=(),
            empty_sources=(),
            failed_sources=("newsapi", "gnews"),
            skipped_sources=(),
        )

    monkeypatch.setattr(service.aggregator, "aggregate_market_sources", fake_aggregate)

    with pytest.raises(NewsProvidersUnavailableError) as exc_info:
        await service.get_market_news(limit=4)

    assert "temporarily unavailable" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_market_news_uses_market_query_mapping(monkeypatch):
    service = NewsService()

    async def fake_aggregate(query: str, limit: int):
        assert query == "india stock earnings"
        return AggregationResult(
            articles=[
                _build_article(
                    "1",
                    "Earnings roundup",
                    "Quarterly results update.",
                    category=NewsCategory.EARNINGS,
                )
            ],
            attempted_sources=("newsapi",),
            successful_sources=("newsapi",),
            empty_sources=(),
            failed_sources=(),
            skipped_sources=("gnews",),
        )

    monkeypatch.setattr(service.aggregator, "aggregate_market_sources", fake_aggregate)
    articles = await service.get_market_news(limit=2, category="earnings")

    assert len(articles) == 1
