from pydantic import BaseModel, Field, computed_field
from typing import Optional, List
from datetime import datetime, timezone
from enum import Enum


class SentimentLabel(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class NewsCategory(str, Enum):
    EARNINGS = "earnings"
    MERGER = "merger"
    MACRO = "macro"
    REGULATORY = "regulatory"
    MARKET_ANALYSIS = "market_analysis"
    INSIDER = "insider_trading"
    GENERAL = "general"


class ImpactLabel(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class MagnitudeLabel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ImpactPrediction(BaseModel):
    predicted_impact: ImpactLabel
    confidence: float = Field(ge=0.0, le=1.0)
    magnitude: MagnitudeLabel
    sector_weight: float = Field(default=1.0)
    reasoning: str


class NewsArticle(BaseModel):
    id: str
    ticker: Optional[str] = None  # None = market-wide news
    title: str
    description: str  # Changed from summary to match design doc
    url: str
    source: str
    published_at: datetime
    image_url: Optional[str] = None
    related_tickers: List[str] = Field(default_factory=list)
    category: NewsCategory
    sentiment: SentimentLabel
    sentiment_score: float = Field(ge=-1.0, le=1.0)  # -1.0 to 1.0
    sentiment_confidence: float = Field(ge=0.0, le=1.0)
    impact_prediction: Optional[ImpactPrediction] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @computed_field(return_type=str)
    @property
    def summary(self) -> str:
        """Temporary compatibility alias for legacy frontend consumers."""
        return self.description


class MarketSentimentSummary(BaseModel):
    ticker: str
    overall_sentiment: SentimentLabel
    sentiment_score: float  # average over last 24h
    article_count: int
    positive_count: int
    negative_count: int
    neutral_count: int
    computed_at: datetime


class NewsListResponse(BaseModel):
    articles: List[NewsArticle]
    total: int
    page: int
    limit: int
    has_more: bool
