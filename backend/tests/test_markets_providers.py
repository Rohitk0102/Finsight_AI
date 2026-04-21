from datetime import datetime, timezone

import httpx
import pytest

from app.schemas.markets import EnrichedNewsArticle, SentimentBadge
from app.schemas.news import NewsArticle, NewsCategory, SentimentLabel
from app.services.markets.providers import GeminiImpactAnalyzer, HuggingFaceImpactAnalyzer


def _article(article_id: str = "provider-test") -> NewsArticle:
    return NewsArticle(
        id=article_id,
        title="Reliance beats estimates",
        description="Strong earnings and margin expansion lifted sentiment.",
        ticker="RELIANCE",
        url=f"https://example.com/{article_id}",
        source="Example",
        published_at=datetime.now(timezone.utc),
        category=NewsCategory.EARNINGS,
        sentiment=SentimentLabel.POSITIVE,
        sentiment_score=0.8,
        sentiment_confidence=0.9,
        related_tickers=["RELIANCE"],
    )


def _fallback_article(article: NewsArticle) -> EnrichedNewsArticle:
    return EnrichedNewsArticle(
        id=article.id,
        title=article.title,
        description=article.description,
        source=article.source,
        sourceUrl=article.url,
        publishedAt=article.published_at,
        category=article.category.value,
        impactScore=55,
        sentimentLabel=SentimentBadge.NEUTRAL,
        aiSummary="Fallback summary.",
        affectedCompanies=[],
        sectorRipple=[],
        primarySymbol=article.ticker,
        bookmarked=False,
    )


class FakeFallback:
    def __init__(self) -> None:
        self.calls = 0

    async def analyze(self, article, primary, peers):
        self.calls += 1
        return _fallback_article(article)


class FakeResponse:
    def __init__(self, status_code: int, payload: dict, *, text: str | None = None) -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = text or ""
        self.headers = {}
        self.request = httpx.Request("POST", "https://example.com")

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("error", request=self.request, response=self)

    def json(self):
        return self._payload


class FakeClient:
    def __init__(self, responses, counter: dict[str, int]) -> None:
        self.responses = responses
        self.counter = counter

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, *args, **kwargs):
        self.counter["count"] += 1
        return self.responses.pop(0)


@pytest.mark.asyncio
async def test_gemini_analyzer_caches_success(monkeypatch):
    fallback = FakeFallback()
    analyzer = GeminiImpactAnalyzer(fallback)
    analyzer.api_key = "test-key"
    article = _article("cache-success")
    call_counter = {"count": 0}

    responses = [
        FakeResponse(
            200,
            {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": '{"impactScore": 81, "sentimentLabel": "bullish", "aiSummary": "Gemini summary."}'
                                }
                            ]
                        }
                    }
                ]
            },
        )
    ]

    monkeypatch.setattr(
        "app.services.markets.providers.httpx.AsyncClient",
        lambda *args, **kwargs: FakeClient(responses, call_counter),
    )

    first = await analyzer.analyze(article, None, [])
    second = await analyzer.analyze(article, None, [])

    assert call_counter["count"] == 1
    assert fallback.calls == 1
    assert first.aiSummary == "Gemini summary."
    assert second.aiSummary == "Gemini summary."


@pytest.mark.asyncio
async def test_gemini_analyzer_sets_quota_cooldown(monkeypatch):
    fallback = FakeFallback()
    analyzer = GeminiImpactAnalyzer(fallback)
    analyzer.api_key = "test-key"
    article = _article("quota-hit")
    call_counter = {"count": 0}

    responses = [
        FakeResponse(
            429,
            {},
            text="Quota exceeded. Please retry in 25.5s.",
        )
    ]

    monkeypatch.setattr(
        "app.services.markets.providers.httpx.AsyncClient",
        lambda *args, **kwargs: FakeClient(responses, call_counter),
    )

    first = await analyzer.analyze(article, None, [])
    second = await analyzer.analyze(article, None, [])

    assert call_counter["count"] == 1
    assert fallback.calls == 2
    assert first.aiSummary == "Fallback summary."
    assert second.aiSummary == "Fallback summary."
    assert analyzer._cooldown_until is not None


@pytest.mark.asyncio
async def test_huggingface_analyzer_caches_success(monkeypatch):
    fallback = FakeFallback()
    analyzer = HuggingFaceImpactAnalyzer(fallback)
    analyzer.api_key = "test-key"
    article = _article("hf-cache-success")
    call_counter = {"count": 0}

    responses = [
        FakeResponse(
            200,
            {
                "choices": [
                    {
                        "message": {
                            "content": '{"impactScore": 79, "sentimentLabel": "bullish", "aiSummary": "HF summary."}'
                        }
                    }
                ]
            },
        )
    ]

    monkeypatch.setattr(
        "app.services.markets.providers.httpx.AsyncClient",
        lambda *args, **kwargs: FakeClient(responses, call_counter),
    )

    first = await analyzer.analyze(article, None, [])
    second = await analyzer.analyze(article, None, [])

    assert call_counter["count"] == 1
    assert fallback.calls == 1
    assert first.aiSummary == "HF summary."
    assert second.aiSummary == "HF summary."


@pytest.mark.asyncio
async def test_huggingface_analyzer_sets_quota_cooldown(monkeypatch):
    fallback = FakeFallback()
    analyzer = HuggingFaceImpactAnalyzer(fallback)
    analyzer.api_key = "test-key"
    article = _article("hf-quota-hit")
    call_counter = {"count": 0}

    responses = [
        FakeResponse(
            429,
            {},
            text="Rate limit exceeded. Retry in 18s.",
        )
    ]

    monkeypatch.setattr(
        "app.services.markets.providers.httpx.AsyncClient",
        lambda *args, **kwargs: FakeClient(responses, call_counter),
    )

    first = await analyzer.analyze(article, None, [])
    second = await analyzer.analyze(article, None, [])

    assert call_counter["count"] == 1
    assert fallback.calls == 2
    assert first.aiSummary == "Fallback summary."
    assert second.aiSummary == "Fallback summary."
    assert analyzer._cooldown_until is not None
