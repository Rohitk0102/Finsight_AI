from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


class MarketStatus(str, Enum):
    LIVE = "live"
    PRE_MARKET = "pre_market"
    AFTER_HOURS = "after_hours"
    CLOSED = "closed"


class ImpactDirection(str, Enum):
    UP = "up"
    DOWN = "down"
    NEUTRAL = "neutral"


class ImpactLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SentimentBadge(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class ChartRange(str, Enum):
    D1 = "1D"
    W1 = "1W"
    M1 = "1M"
    M3 = "3M"
    M6 = "6M"
    Y1 = "1Y"
    Y5 = "5Y"


class ChartMode(str, Enum):
    LINE = "line"
    CANDLE = "candle"


class SymbolIdentity(BaseModel):
    symbol: str
    displaySymbol: str
    exchange: str
    companyName: str
    logoUrl: Optional[str] = None
    sector: Optional[str] = None


class PriceSnapshot(SymbolIdentity):
    currentPrice: float
    change: float
    changePct: float
    marketStatus: MarketStatus
    lastUpdated: datetime
    volume: Optional[int] = None
    previousClose: Optional[float] = None


class SearchResult(PriceSnapshot):
    keywordMatch: Optional[str] = None


class SearchContextResponse(BaseModel):
    recent: list[SymbolIdentity]
    trending: list[PriceSnapshot]


class MarketIndexCard(BaseModel):
    symbol: str
    label: str
    value: float
    change: float
    changePct: float
    sparkline: list[float] = Field(default_factory=list)


class MarketMover(PriceSnapshot):
    marketCap: Optional[float] = None
    marketCapBucket: Optional[str] = None


class SectorHeatmapCell(BaseModel):
    sector: str
    changePct: float
    leaders: list[str] = Field(default_factory=list)


class FiiDiiActivity(BaseModel):
    sessionDate: str
    fiiNet: float
    diiNet: float


class IpoTrackerItem(BaseModel):
    id: str
    name: str
    status: Literal["upcoming", "ongoing", "listed"]
    exchange: str
    openDate: Optional[str] = None
    closeDate: Optional[str] = None
    listingDate: Optional[str] = None
    priceBand: Optional[str] = None
    gmp: Optional[float] = None


class EconomicCalendarEvent(BaseModel):
    id: str
    title: str
    category: str
    scheduledAt: datetime
    impact: Literal["high", "medium", "low"]
    market: str = "India"


class AffectedCompany(BaseModel):
    symbol: str
    displaySymbol: str
    companyName: str
    direction: ImpactDirection
    impactLevel: ImpactLevel


class SectorRipple(BaseModel):
    sector: str
    direction: ImpactDirection
    impactLevel: ImpactLevel


class EnrichedNewsArticle(BaseModel):
    id: str
    title: str
    description: str
    source: str
    sourceUrl: str
    publishedAt: datetime
    imageUrl: Optional[str] = None
    category: str
    impactScore: int = Field(ge=0, le=100)
    sentimentLabel: SentimentBadge
    aiSummary: str
    affectedCompanies: list[AffectedCompany] = Field(default_factory=list)
    sectorRipple: list[SectorRipple] = Field(default_factory=list)
    primarySymbol: Optional[str] = None
    bookmarked: bool = False


class MarketNewsFeedResponse(BaseModel):
    articles: list[EnrichedNewsArticle]
    total: int
    page: int
    limit: int
    hasMore: bool


class KeyStats(BaseModel):
    marketCap: Optional[float] = None
    peRatio: Optional[float] = None
    eps: Optional[float] = None
    dividendYield: Optional[float] = None
    beta: Optional[float] = None
    bookValue: Optional[float] = None
    week52High: Optional[float] = None
    week52Low: Optional[float] = None
    avgVolume: Optional[int] = None


class AnalystConsensus(BaseModel):
    rating: str
    buy: int
    hold: int
    sell: int
    targetPrice: Optional[float] = None


class PeerComparisonItem(BaseModel):
    symbol: str
    displaySymbol: str
    companyName: str
    sector: Optional[str] = None
    currentPrice: float
    changePct: float
    peRatio: Optional[float] = None
    marketCap: Optional[float] = None


class FinancialMetricPoint(BaseModel):
    period: str
    revenue: Optional[float] = None
    netProfit: Optional[float] = None
    operatingCashFlow: Optional[float] = None


class FinancialsSnapshot(BaseModel):
    quarterly: list[FinancialMetricPoint] = Field(default_factory=list)
    annual: list[FinancialMetricPoint] = Field(default_factory=list)


class ShareholdingSlice(BaseModel):
    label: str
    percent: float
    color: str


class PortfolioPosition(BaseModel):
    quantity: float
    averagePrice: float
    currentValue: float
    investedValue: float
    unrealizedPnl: float
    unrealizedPnlPct: float
    dayChangePct: float


class CompanyAbout(BaseModel):
    description: Optional[str] = None
    ceo: Optional[str] = None
    founded: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    employees: Optional[int] = None
    headquarters: Optional[str] = None


class CompanyDetailResponse(BaseModel):
    profile: PriceSnapshot
    stats: KeyStats
    about: CompanyAbout = Field(default_factory=CompanyAbout)
    analystConsensus: AnalystConsensus
    peers: list[PeerComparisonItem] = Field(default_factory=list)
    financials: FinancialsSnapshot
    shareholding: list[ShareholdingSlice] = Field(default_factory=list)
    portfolioPosition: Optional[PortfolioPosition] = None


class ChartPoint(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    sma20: Optional[float] = None
    ema20: Optional[float] = None
    rsi14: Optional[float] = None
    macd: Optional[float] = None
    macdSignal: Optional[float] = None
    bbUpper: Optional[float] = None
    bbLower: Optional[float] = None


class CompanyChartResponse(BaseModel):
    symbol: str
    range: ChartRange
    mode: ChartMode = ChartMode.CANDLE
    supportsRealtime: bool = True
    points: list[ChartPoint] = Field(default_factory=list)


class MarketOverviewResponse(BaseModel):
    marketStatus: MarketStatus
    indices: list[MarketIndexCard]
    watchlist: list[PriceSnapshot]
    topGainers: list[MarketMover]
    topLosers: list[MarketMover]
    mostActive: list[MarketMover]
    sectorHeatmap: list[SectorHeatmapCell]
    fiiDiiActivity: FiiDiiActivity
    ipoTracker: list[IpoTrackerItem]
    economicCalendar: list[EconomicCalendarEvent]
    latestNews: list[EnrichedNewsArticle]
    breakingNewsCount: int = 0


class MarketWatchlistEntry(BaseModel):
    symbol: str
    exchange: str = "NSE"
    notes: Optional[str] = None


class BookmarkCreate(BaseModel):
    articleId: str
    title: str
    sourceUrl: str
    source: str
    publishedAt: datetime


class PriceAlertCreate(BaseModel):
    symbol: str
    exchange: str = "NSE"
    alertType: Literal["price_above", "price_below", "pct_change"]
    thresholdValue: float


class PriceAlertResponse(BaseModel):
    id: str
    symbol: str
    exchange: str
    alertType: str
    thresholdValue: float
    isActive: bool = True
    createdAt: datetime


class MutationResponse(BaseModel):
    success: bool = True
    message: str


class BookmarkRecord(BaseModel):
    id: str
    article_id: str
    title: str
    source: Optional[str] = None
    source_url: str
    published_at: datetime
    created_at: Optional[datetime] = None


class MarketSocketMessage(BaseModel):
    type: Literal["quote_update", "subscribed", "unsubscribed", "heartbeat", "error"]
    symbols: list[str] = Field(default_factory=list)
    quotes: list[PriceSnapshot] = Field(default_factory=list)
    message: Optional[str] = None
