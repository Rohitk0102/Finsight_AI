export type MarketStatus = "live" | "pre_market" | "after_hours" | "closed";
export type ChartRange = "1D" | "1W" | "1M" | "3M" | "6M" | "1Y" | "5Y";
export type ChartMode = "line" | "candle";
export type IndicatorKey = "SMA" | "EMA" | "RSI" | "MACD" | "Bollinger";

export interface SymbolIdentity {
  symbol: string;
  displaySymbol: string;
  exchange: string;
  companyName: string;
  logoUrl?: string | null;
  sector?: string | null;
}

export interface PriceSnapshot extends SymbolIdentity {
  currentPrice: number;
  change: number;
  changePct: number;
  marketStatus: MarketStatus;
  lastUpdated: string;
  volume?: number | null;
  previousClose?: number | null;
}

export interface SearchResult extends PriceSnapshot {
  keywordMatch?: string | null;
}

export interface SearchContextResponse {
  recent: SymbolIdentity[];
  trending: PriceSnapshot[];
}

export interface MarketIndexCard {
  symbol: string;
  label: string;
  value: number;
  change: number;
  changePct: number;
  sparkline: number[];
}

export interface MarketMover extends PriceSnapshot {
  marketCap?: number | null;
  marketCapBucket?: string | null;
}

export interface SectorHeatmapCell {
  sector: string;
  changePct: number;
  leaders: string[];
}

export interface FiiDiiActivity {
  sessionDate: string;
  fiiNet: number;
  diiNet: number;
}

export interface IpoTrackerItem {
  id: string;
  name: string;
  status: "upcoming" | "ongoing" | "listed";
  exchange: string;
  openDate?: string | null;
  closeDate?: string | null;
  listingDate?: string | null;
  priceBand?: string | null;
  gmp?: number | null;
}

export interface EconomicCalendarEvent {
  id: string;
  title: string;
  category: string;
  scheduledAt: string;
  impact: "high" | "medium" | "low";
  market: string;
}

export interface AffectedCompany {
  symbol: string;
  displaySymbol: string;
  companyName: string;
  direction: "up" | "down" | "neutral";
  impactLevel: "high" | "medium" | "low";
}

export interface SectorRipple {
  sector: string;
  direction: "up" | "down" | "neutral";
  impactLevel: "high" | "medium" | "low";
}

export interface EnrichedNewsArticle {
  id: string;
  title: string;
  description: string;
  source: string;
  sourceUrl: string;
  publishedAt: string;
  imageUrl?: string | null;
  category: string;
  impactScore: number;
  sentimentLabel: "bullish" | "bearish" | "neutral";
  aiSummary: string;
  affectedCompanies: AffectedCompany[];
  sectorRipple: SectorRipple[];
  primarySymbol?: string | null;
  bookmarked?: boolean;
}

export interface MarketNewsFeedResponse {
  articles: EnrichedNewsArticle[];
  total: number;
  page: number;
  limit: number;
  hasMore: boolean;
}

export interface KeyStats {
  marketCap?: number | null;
  peRatio?: number | null;
  eps?: number | null;
  dividendYield?: number | null;
  beta?: number | null;
  bookValue?: number | null;
  week52High?: number | null;
  week52Low?: number | null;
  avgVolume?: number | null;
}

export interface AnalystConsensus {
  rating: string;
  buy: number;
  hold: number;
  sell: number;
  targetPrice?: number | null;
}

export interface PeerComparisonItem {
  symbol: string;
  displaySymbol: string;
  companyName: string;
  sector?: string | null;
  currentPrice: number;
  changePct: number;
  peRatio?: number | null;
  marketCap?: number | null;
}

export interface FinancialMetricPoint {
  period: string;
  revenue?: number | null;
  netProfit?: number | null;
  operatingCashFlow?: number | null;
}

export interface FinancialsSnapshot {
  quarterly: FinancialMetricPoint[];
  annual: FinancialMetricPoint[];
}

export interface ShareholdingSlice {
  label: string;
  percent: number;
  color: string;
}

export interface PortfolioPosition {
  quantity: number;
  averagePrice: number;
  currentValue: number;
  investedValue: number;
  unrealizedPnl: number;
  unrealizedPnlPct: number;
  dayChangePct: number;
}

export interface CompanyDetailResponse {
  profile: PriceSnapshot;
  stats: KeyStats;
  analystConsensus: AnalystConsensus;
  peers: PeerComparisonItem[];
  financials: FinancialsSnapshot;
  shareholding: ShareholdingSlice[];
  portfolioPosition?: PortfolioPosition | null;
  about?: any;
}

export interface ChartPoint {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  sma20?: number | null;
  ema20?: number | null;
  rsi14?: number | null;
  macd?: number | null;
  macdSignal?: number | null;
  bbUpper?: number | null;
  bbLower?: number | null;
}

export interface CompanyChartResponse {
  symbol: string;
  range: ChartRange;
  mode: ChartMode;
  supportsRealtime: boolean;
  points: ChartPoint[];
}

export interface MarketOverviewResponse {
  marketStatus: MarketStatus;
  indices: MarketIndexCard[];
  watchlist: PriceSnapshot[];
  topGainers: MarketMover[];
  topLosers: MarketMover[];
  mostActive: MarketMover[];
  sectorHeatmap: SectorHeatmapCell[];
  fiiDiiActivity: FiiDiiActivity;
  ipoTracker: IpoTrackerItem[];
  economicCalendar: EconomicCalendarEvent[];
  latestNews: EnrichedNewsArticle[];
  breakingNewsCount: number;
}

export interface PriceAlert {
  id: string;
  symbol: string;
  exchange: string;
  alertType: "price_above" | "price_below" | "pct_change";
  thresholdValue: number;
  isActive: boolean;
  createdAt: string;
}

export interface MarketSocketMessage {
  type: "quote_update" | "subscribed" | "unsubscribed" | "heartbeat" | "error";
  symbols: string[];
  quotes: PriceSnapshot[];
  message?: string | null;
}
