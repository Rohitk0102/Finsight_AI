"""
News service: orchestrates multi-source aggregation and lightweight sentiment scoring.
"""
from datetime import datetime, timezone
from typing import Optional


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
from app.schemas.news import NewsArticle, MarketSentimentSummary, SentimentLabel, NewsCategory
from app.services.news.aggregator import AggregationResult, NewsAggregator
from loguru import logger


class NewsProvidersUnavailableError(RuntimeError):
    """Raised when upstream news providers fail and no usable payload is available."""


class NewsService:
    def __init__(self, aggregator: Optional[NewsAggregator] = None):
        self.aggregator = aggregator or NewsAggregator()

    async def get_stock_news(self, ticker: str, limit: int = 10) -> list[NewsArticle]:
        ticker = ticker.upper()
        result = await self.aggregator.aggregate_ticker_sources(
            query=ticker,
            limit=max(limit * 3, limit),
        )
        self._raise_for_provider_failures(result, context=f"ticker {ticker}")

        return self._finalize_articles(
            result.articles,
            limit=limit,
            ticker_override=ticker,
            clear_ticker=False,
        )

    async def get_market_news(self, limit: int = 20, category: Optional[str] = None) -> list[NewsArticle]:
        query = self._build_market_query(category)
        result = await self.aggregator.aggregate_market_sources(
            query=query,
            limit=max(limit * 3, limit),
        )
        self._raise_for_provider_failures(result, context="market news")

        articles = self._finalize_articles(
            result.articles,
            limit=max(limit * 2, limit),
            ticker_override=None,
            clear_ticker=True,
        )

        requested_category = self._parse_category_filter(category)
        if requested_category is not None:
            articles = [a for a in articles if a.category == requested_category]

        return articles[:limit]

    async def get_sentiment_summary(self, ticker: str) -> MarketSentimentSummary:
        articles = await self.get_stock_news(ticker, limit=30)
        if not articles:
            return MarketSentimentSummary(
                ticker=ticker, overall_sentiment=SentimentLabel.NEUTRAL,
                sentiment_score=0.0, article_count=0,
                positive_count=0, negative_count=0, neutral_count=0,
                computed_at=datetime.now(timezone.utc),
            )

        scores = [a.sentiment_score for a in articles]
        avg_score = sum(scores) / len(scores)
        pos = sum(1 for a in articles if a.sentiment == SentimentLabel.POSITIVE)
        neg = sum(1 for a in articles if a.sentiment == SentimentLabel.NEGATIVE)
        neu = len(articles) - pos - neg

        if avg_score > 0.1:
            overall = SentimentLabel.POSITIVE
        elif avg_score < -0.1:
            overall = SentimentLabel.NEGATIVE
        else:
            overall = SentimentLabel.NEUTRAL

        return MarketSentimentSummary(
            ticker=ticker, overall_sentiment=overall,
            sentiment_score=round(avg_score, 4),
            article_count=len(articles),
            positive_count=pos, negative_count=neg, neutral_count=neu,
            computed_at=datetime.now(timezone.utc),
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _finalize_articles(
        self,
        articles: list[NewsArticle],
        limit: int,
        ticker_override: Optional[str],
        clear_ticker: bool,
    ) -> list[NewsArticle]:
        seen_titles: set[str] = set()
        finalized: list[NewsArticle] = []

        for article in sorted(articles, key=lambda x: _as_utc(x.published_at), reverse=True):
            title_key = article.title.strip().lower()
            if title_key in seen_titles:
                continue
            seen_titles.add(title_key)

            sentiment, score = self._simple_sentiment(f"{article.title} {article.description}")
            confidence = round(min(max(abs(score), 0.0), 1.0), 4)

            if clear_ticker:
                ticker = None
                related_tickers = []
            elif ticker_override:
                ticker = ticker_override
                related_tickers = list({*article.related_tickers, ticker_override})
            else:
                ticker = article.ticker
                related_tickers = article.related_tickers

            finalized.append(
                article.model_copy(
                    update={
                        "ticker": ticker,
                        "related_tickers": related_tickers,
                        "sentiment": sentiment,
                        "sentiment_score": score,
                        "sentiment_confidence": confidence,
                    }
                )
            )

            if len(finalized) >= limit:
                break

        return finalized

    def _simple_sentiment(self, text: str) -> tuple[SentimentLabel, float]:
        """
        Rule-based fallback. Replace with FinBERT in production
        by loading transformers pipeline once at startup.
        """
        text_lower = text.lower()
        positive_words = {"gain", "rise", "surge", "growth", "profit", "beat", "bullish",
                          "positive", "strong", "up", "high", "record", "exceed"}
        negative_words = {"loss", "fall", "drop", "decline", "miss", "bearish", "weak",
                          "down", "low", "crash", "risk", "concern", "cut", "layoff"}
        pos = sum(1 for w in positive_words if w in text_lower)
        neg = sum(1 for w in negative_words if w in text_lower)
        if pos > neg:
            return SentimentLabel.POSITIVE, round(min(pos * 0.2, 1.0), 4)
        elif neg > pos:
            return SentimentLabel.NEGATIVE, round(max(-neg * 0.2, -1.0), 4)
        return SentimentLabel.NEUTRAL, 0.0

    def _parse_category_filter(self, raw: Optional[str]) -> Optional[NewsCategory]:
        if not raw:
            return None
        normalized = raw.strip().lower()
        mapping = {
            "general": NewsCategory.GENERAL,
            "market_analysis": NewsCategory.MARKET_ANALYSIS,
            "earnings": NewsCategory.EARNINGS,
            "merger": NewsCategory.MERGER,
            "macro": NewsCategory.MACRO,
            "regulatory": NewsCategory.REGULATORY,
            "insider_trading": NewsCategory.INSIDER,
            "insider": NewsCategory.INSIDER,
        }
        return mapping.get(normalized)

    def _build_market_query(self, category: Optional[str]) -> str:
        if not category:
            return "stock market india"

        normalized = category.strip().lower()
        mapping = {
            "general": "stock market india",
            "market_analysis": "india stock market analysis",
            "earnings": "india stock earnings",
            "merger": "india mergers acquisitions stocks",
            "macro": "india economy stock market",
            "regulatory": "india market regulation stocks",
            "insider_trading": "india insider trading stocks",
            "insider": "india insider trading stocks",
        }
        return mapping.get(normalized, f"{normalized} india stock market")

    def _raise_for_provider_failures(self, result: AggregationResult, *, context: str) -> None:
        if result.articles:
            if result.failed_sources:
                logger.warning(
                    "Partial provider degradation for {}. failed_sources={}",
                    context,
                    ",".join(result.failed_sources),
                )
            return

        if result.failed_sources:
            failed = ", ".join(result.failed_sources)
            raise NewsProvidersUnavailableError(
                f"News providers are temporarily unavailable for {context}. Failed sources: {failed}."
            )

        if not result.attempted_sources:
            raise NewsProvidersUnavailableError(
                "No news providers are configured for this environment."
            )
