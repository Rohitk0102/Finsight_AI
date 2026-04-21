from datetime import datetime, timezone

import pytest

from app.schemas.markets import (
    AffectedCompany,
    EnrichedNewsArticle,
    ImpactDirection,
    ImpactLevel,
    MarketNewsFeedResponse,
    SectorRipple,
    SentimentBadge,
)
from app.schemas.news import NewsArticle, NewsCategory, SentimentLabel
from app.services.markets.service import MarketPulseService


def _market_article(article_id: str, title: str) -> NewsArticle:
    return NewsArticle(
        id=article_id,
        title=title,
        description=f"{title} description",
        ticker=None,
        url=f"https://example.com/{article_id}",
        source="Example",
        published_at=datetime.now(timezone.utc),
        category=NewsCategory.MARKET_ANALYSIS,
        sentiment=SentimentLabel.POSITIVE,
        sentiment_score=0.6,
        sentiment_confidence=0.9,
        related_tickers=[],
    )


def _enriched_article(
    article_id: str,
    *,
    symbol: str,
    sector: str,
    exchange: str,
    market_cap_bucket: str,
    sentiment: SentimentBadge,
) -> EnrichedNewsArticle:
    direction = ImpactDirection.UP if sentiment == SentimentBadge.BULLISH else ImpactDirection.DOWN
    return EnrichedNewsArticle(
        id=article_id,
        title=f"{symbol} headline",
        description="AI summary ready",
        source="Example",
        sourceUrl=f"https://example.com/{article_id}",
        publishedAt=datetime.now(timezone.utc),
        category="market_analysis",
        impactScore=84,
        sentimentLabel=sentiment,
        aiSummary="Signal summary",
        affectedCompanies=[
            AffectedCompany(
                symbol=f"{symbol}.NS",
                displaySymbol=symbol,
                companyName=f"{symbol} Ltd",
                direction=direction,
                impactLevel=ImpactLevel.HIGH,
            )
        ],
        sectorRipple=[SectorRipple(sector=sector, direction=direction, impactLevel=ImpactLevel.HIGH)],
        primarySymbol=symbol,
        bookmarked=False,
    )


@pytest.mark.asyncio
async def test_news_feed_applies_company_filters(monkeypatch):
    service = MarketPulseService()
    raw_articles = [_market_article("a1", "Reliance rally"), _market_article("a2", "TCS under pressure")]
    enriched_map = {
        "a1": _enriched_article(
            "a1",
            symbol="RELIANCE",
            sector="Energy",
            exchange="NSE",
            market_cap_bucket="large",
            sentiment=SentimentBadge.BULLISH,
        ),
        "a2": _enriched_article(
            "a2",
            symbol="TCS",
            sector="IT",
            exchange="NSE",
            market_cap_bucket="large",
            sentiment=SentimentBadge.BEARISH,
        ),
    }

    async def fake_market_news(*_args, **_kwargs):
        return raw_articles

    async def fake_analyze(article, *_args, **_kwargs):
        return enriched_map[article.id]

    async def fake_company_context(_symbols):
        return {
            "RELIANCE": {"symbol": "RELIANCE", "exchange": "NSE", "sector": "energy", "marketCapBucket": "large"},
            "TCS": {"symbol": "TCS", "exchange": "NSE", "sector": "it", "marketCapBucket": "large"},
        }

    monkeypatch.setattr(service.news_provider, "get_market_news", fake_market_news)
    monkeypatch.setattr(service.impact_analyzer, "analyze", fake_analyze)
    monkeypatch.setattr(service, "_build_company_context", fake_company_context)

    result = await service.get_news_feed(
        page=1,
        limit=10,
        category=None,
        sentiment="bullish",
        sector="energy",
        exchange="NSE",
        market_cap="large",
        bookmarked_urls={"https://example.com/a1"},
    )

    assert isinstance(result, MarketNewsFeedResponse)
    assert result.total == 1
    assert result.articles[0].primarySymbol == "RELIANCE"
    assert result.articles[0].bookmarked is True


@pytest.mark.asyncio
async def test_news_feed_paginates_filtered_results(monkeypatch):
    service = MarketPulseService()
    raw_articles = [_market_article("a1", "One"), _market_article("a2", "Two"), _market_article("a3", "Three")]

    async def fake_market_news(*_args, **_kwargs):
        return raw_articles

    async def fake_analyze(article, *_args, **_kwargs):
        return _enriched_article(
            article.id,
            symbol=f"SYM{article.id[-1]}",
            sector="Market",
            exchange="NSE",
            market_cap_bucket="large",
            sentiment=SentimentBadge.BULLISH,
        )

    monkeypatch.setattr(service.news_provider, "get_market_news", fake_market_news)
    monkeypatch.setattr(service.impact_analyzer, "analyze", fake_analyze)

    result = await service.get_news_feed(
        page=2,
        limit=1,
        category=None,
        sentiment=None,
        sector=None,
        exchange=None,
        market_cap=None,
        bookmarked_urls=set(),
    )

    assert result.total == 3
    assert result.page == 2
    assert len(result.articles) == 1
    assert result.hasMore is True
