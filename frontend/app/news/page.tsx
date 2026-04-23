"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { newsApi, marketsApi } from "@/lib/api/client";
import {
  ExternalLink,
  TrendingUp,
  TrendingDown,
  Minus,
  Newspaper,
  Search,
  X,
  PieChart,
  BarChart3,
  Activity,
  Flame,
  ArrowUpRight,
  ArrowDownRight,
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { toast } from "sonner";
import { cn, formatPercent } from "@/lib/utils";
import { Pagination } from "@/components/ui/pagination";
import type { MarketOverviewResponse, MarketMover, SectorHeatmapCell } from "@/lib/markets/types";

interface Article {
  id: string;
  ticker: string | null;
  title: string;
  description?: string;
  summary?: string;
  url: string;
  source: string;
  published_at: string;
  sentiment: "positive" | "negative" | "neutral";
  sentiment_score: number;
  category: string;
  image_url: string | null;
}

interface NewsListResponse {
  articles: Article[];
  total: number;
  page: number;
  limit: number;
  has_more: boolean;
}

type TimeRange = "all" | "1h" | "6h" | "24h" | "7d" | "30d";
type CategoryFilter = "all" | "general" | "earnings" | "merger" | "macro" | "regulatory" | "market_analysis";
type SentimentFilter = "all" | "positive" | "negative" | "neutral";

interface FilterState {
  ticker: string;
  category: CategoryFilter;
  sentiment: SentimentFilter;
  timeRange: TimeRange;
}

const sentimentConfig = {
  positive: { icon: TrendingUp,   color: "#22C55E", badge: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",  label: "Positive" },
  negative: { icon: TrendingDown, color: "#EF4444", badge: "bg-rose-500/10 text-rose-500 border-rose-500/20",    label: "Negative" },
  neutral:  { icon: Minus,        color: "#f59e0b", badge: "bg-amber-500/10 text-amber-500 border-amber-500/20",  label: "Neutral"  },
};

function ArticleThumbnail({ src, alt }: { src: string; alt: string }) {
  const [hidden, setHidden] = useState(false);
  if (!src || hidden) return <div className="w-24 h-24 rounded-xl bg-muted flex items-center justify-center flex-shrink-0 hidden sm:flex"><Newspaper className="h-6 w-6 text-muted-foreground/40" /></div>;

  return (
    <div className="w-24 h-24 relative rounded-xl overflow-hidden flex-shrink-0 hidden sm:block">
      <img
        src={src}
        alt={alt}
        className="w-full h-full object-cover"
        loading="lazy"
        referrerPolicy="no-referrer"
        onError={() => setHidden(true)}
      />
    </div>
  );
}

export default function NewsPage() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [overview, setOverview] = useState<MarketOverviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [sidebarLoading, setSidebarLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize]    = useState(10);
  const [filters, setFilters] = useState<FilterState>({
    ticker: "",
    category: "all",
    sentiment: "all",
    timeRange: "all",
  });
  const [inputVal, setInputVal] = useState("");

  useEffect(() => {
    fetchNews(filters, 1);
    fetchOverview();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const fetchOverview = async () => {
    try {
      setSidebarLoading(true);
      const res = await marketsApi.overview();
      setOverview(res.data);
    } catch (err) {
      console.error("Failed to fetch sidebar overview", err);
    } finally {
      setSidebarLoading(false);
    }
  };

  const fetchNews = async (activeFilters: FilterState, page: number) => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const params: any = { page, limit: pageSize };
      if (activeFilters.ticker) params.ticker = activeFilters.ticker;
      if (activeFilters.category !== "all") params.category = activeFilters.category;
      if (activeFilters.sentiment !== "all") params.sentiment = activeFilters.sentiment;
      if (activeFilters.timeRange !== "all") params.time_range = activeFilters.timeRange;

      const res = await newsApi.list(params);
      const payload = res.data as NewsListResponse;
      setArticles(payload.articles ?? []);
      setTotalCount(payload.total ?? payload.articles?.length ?? 0);
      setCurrentPage(page);
    } catch (error: any) {
      setArticles([]);
      setTotalCount(0);
      setErrorMessage(error?.response?.status === 503 ? "News service temporarily unavailable" : "Failed to load news");
    } finally {
      setLoading(false);
    }
  };

  const updateFilter = <K extends keyof FilterState>(key: K, value: FilterState[K]) => {
    const next = { ...filters, [key]: value };
    setFilters(next);
    fetchNews(next, 1);
  };

  const handleFilter = () => {
    const next = { ...filters, ticker: inputVal.trim().toUpperCase() };
    setFilters(next);
    fetchNews(next, 1);
  };

  const handleClear = () => {
    setInputVal("");
    const next: FilterState = { ticker: "", category: "all", sentiment: "all", timeRange: "all" };
    setFilters(next);
    fetchNews(next, 1);
  };

  const handlePageChange = (page: number) => {
    fetchNews(filters, page);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  // Derived sentiment stats
  const avgSentiment = articles.length > 0
    ? articles.reduce((acc, a) => acc + a.sentiment_score, 0) / articles.length
    : 0;

  return (
    <div className="max-w-[1440px] mx-auto px-4 lg:px-8 py-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Market Pulse News</h1>
          <p className="text-muted-foreground mt-1">
            Real-time financial intelligence with AI-driven sentiment analysis
          </p>
        </div>
        <div className="flex items-center gap-3">
          {!loading && (
            <div className="px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-semibold">
              {totalCount} Articles
            </div>
          )}
          <div className={cn(
            "px-3 py-1 rounded-full border text-xs font-semibold flex items-center gap-1.5",
            avgSentiment > 0.1 ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20" :
            avgSentiment < -0.1 ? "bg-rose-500/10 text-rose-500 border-rose-500/20" :
            "bg-amber-500/10 text-amber-500 border-amber-500/20"
          )}>
            <Activity className="h-3.5 w-3.5" />
            Market Mood: {avgSentiment > 0.1 ? "Positive" : avgSentiment < -0.1 ? "Negative" : "Neutral"} ({avgSentiment.toFixed(2)})
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* LEFT COLUMN: Main Feed */}
        <div className="lg:col-span-8 space-y-6">
          
          {/* Filter Bar */}
          <div className="card-surface p-5 animate-slide-in-up">
            <div className="flex flex-col md:flex-row gap-3">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <input
                  value={inputVal}
                  onChange={(e) => setInputVal(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleFilter()}
                  placeholder="Search ticker (e.g. RELIANCE, TCS)"
                  className="input-field pl-10 pr-10 bg-background/50 border-none ring-1 ring-border focus:ring-2 focus:ring-primary"
                />
                {inputVal && (
                  <button onClick={handleClear} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"><X className="h-4 w-4" /></button>
                )}
              </div>
              <div className="flex gap-2">
                <button onClick={handleFilter} className="btn-primary flex-1 md:flex-none">Apply</button>
                <button onClick={handleClear} className="btn-secondary px-3"><X className="h-4 w-4" /></button>
              </div>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mt-4">
              <div className="space-y-1.5">
                <label className="text-[10px] uppercase tracking-wider font-bold text-muted-foreground ml-1">Category</label>
                <select
                  value={filters.category}
                  onChange={(e) => updateFilter("category", e.target.value as CategoryFilter)}
                  className="input-field bg-background/50 text-xs py-2"
                >
                  <option value="all">All News</option>
                  <option value="earnings">Earnings</option>
                  <option value="merger">Merger</option>
                  <option value="macro">Economy</option>
                  <option value="regulatory">Regulatory</option>
                  <option value="market_analysis">Analysis</option>
                </select>
              </div>
              <div className="space-y-1.5">
                <label className="text-[10px] uppercase tracking-wider font-bold text-muted-foreground ml-1">Sentiment</label>
                <select
                  value={filters.sentiment}
                  onChange={(e) => updateFilter("sentiment", e.target.value as SentimentFilter)}
                  className="input-field bg-background/50 text-xs py-2"
                >
                  <option value="all">All Sentiment</option>
                  <option value="positive">Bullish</option>
                  <option value="neutral">Neutral</option>
                  <option value="negative">Bearish</option>
                </select>
              </div>
              <div className="space-y-1.5 col-span-2 md:col-span-1">
                <label className="text-[10px] uppercase tracking-wider font-bold text-muted-foreground ml-1">Time Range</label>
                <select
                  value={filters.timeRange}
                  onChange={(e) => updateFilter("timeRange", e.target.value as TimeRange)}
                  className="input-field bg-background/50 text-xs py-2"
                >
                  <option value="all">Any Time</option>
                  <option value="1h">Last hour</option>
                  <option value="24h">Last 24h</option>
                  <option value="7d">Last week</option>
                </select>
              </div>
            </div>
          </div>

          {/* Articles Feed */}
          <div className="space-y-4">
            {loading ? (
              Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="card-surface p-5 flex gap-4">
                  <div className="skeleton w-24 h-24 rounded-xl flex-shrink-0" />
                  <div className="flex-1 space-y-3">
                    <div className="flex justify-between"><div className="skeleton h-3 w-20 rounded" /><div className="skeleton h-3 w-16 rounded" /></div>
                    <div className="skeleton h-5 w-full rounded" />
                    <div className="skeleton h-4 w-3/4 rounded" />
                  </div>
                </div>
              ))
            ) : articles.length === 0 ? (
              <div className="card-surface py-20 text-center">
                <Newspaper className="h-12 w-12 text-muted-foreground/20 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-foreground">No matching stories</h3>
                <p className="text-muted-foreground text-sm max-w-xs mx-auto mt-1">Try adjusting your filters or searching for a different ticker.</p>
              </div>
            ) : (
              articles.map((a, i) => {
                const cfg = sentimentConfig[a.sentiment];
                const SentIcon = cfg.icon;
                return (
                  <a
                    key={a.id}
                    href={a.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block group card-surface p-5 hover:border-primary/30 transition-all duration-300 animate-slide-in-up"
                    style={{ animationDelay: `${Math.min(i * 30, 300)}ms` }}
                  >
                    <div className="flex flex-col sm:flex-row gap-5">
                      <ArticleThumbnail src={a.image_url!} alt={a.title} />
                      <div className="flex-1 min-w-0">
                        <div className="flex flex-wrap items-center gap-2 mb-3">
                          {a.ticker && (
                            <Link href={`/markets/${a.ticker}`} className="badge bg-primary/10 text-primary hover:bg-primary/20 transition-colors border-none py-1">
                              ${a.ticker}
                            </Link>
                          )}
                          <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground bg-muted px-2 py-0.5 rounded flex items-center gap-1.5">
                            {a.category.replace("_", " ")}
                          </span>
                          <div className={cn("badge ml-auto border py-1", cfg.badge)}>
                            <SentIcon className="h-3 w-3" />
                            {cfg.label}
                            <span className="opacity-70 ml-1">
                              {a.sentiment_score > 0 ? "+" : ""}{a.sentiment_score.toFixed(2)}
                            </span>
                          </div>
                        </div>

                        <h3 className="text-lg font-bold leading-tight group-hover:text-primary transition-colors line-clamp-2 mb-2">
                          {a.title}
                        </h3>

                        <p className="text-sm text-muted-foreground line-clamp-2 mb-4 leading-relaxed">
                          {a.description || a.summary}
                        </p>

                        <div className="flex items-center justify-between mt-auto pt-3 border-t border-border/50 text-[11px] text-muted-foreground font-medium">
                          <div className="flex items-center gap-2">
                            <span className="text-foreground">{a.source}</span>
                            <span className="text-muted-foreground/30">•</span>
                            <span>{formatDistanceToNow(new Date(a.published_at), { addSuffix: true })}</span>
                          </div>
                          <span className="inline-flex items-center gap-1 text-primary opacity-0 group-hover:opacity-100 transition-opacity translate-x-2 group-hover:translate-x-0 duration-300">
                            Read Article <ArrowUpRight className="h-3 w-3" />
                          </span>
                        </div>
                      </div>
                    </div>
                  </a>
                );
              })
            )}

            <Pagination
              currentPage={currentPage}
              totalCount={totalCount}
              pageSize={pageSize}
              onPageChange={handlePageChange}
            />
          </div>
        </div>

        {/* RIGHT COLUMN: Sidebar */}
        <aside className="lg:col-span-4 space-y-6">
          
          {/* Sentiment Summary Card */}
          <div className="card-surface p-5 bg-gradient-to-br from-card to-primary/5 border-primary/10 overflow-hidden relative">
            <div className="relative z-10">
              <div className="flex items-center gap-2 mb-4">
                <div className="p-2 rounded-lg bg-primary/10 text-primary">
                  <BarChart3 className="h-5 w-5" />
                </div>
                <h4 className="font-bold text-sm">Sentiment Overview</h4>
              </div>
              
              <div className="flex items-end gap-4 mb-6">
                <div className="text-4xl font-bold tracking-tighter">
                  {avgSentiment.toFixed(2)}
                </div>
                <div className="mb-1">
                  <div className={cn(
                    "text-xs font-bold uppercase",
                    avgSentiment > 0.1 ? "text-emerald-500" : avgSentiment < -0.1 ? "text-rose-500" : "text-amber-500"
                  )}>
                    {avgSentiment > 0.1 ? "Bullish" : avgSentiment < -0.1 ? "Bearish" : "Neutral"}
                  </div>
                  <div className="text-[10px] text-muted-foreground">Across {articles.length} news stories</div>
                </div>
              </div>

              <div className="space-y-3">
                <SentimentBar 
                  label="Positive" 
                  count={articles.filter(a => a.sentiment === "positive").length} 
                  total={articles.length} 
                  color="bg-emerald-500"
                />
                <SentimentBar 
                  label="Neutral" 
                  count={articles.filter(a => a.sentiment === "neutral").length} 
                  total={articles.length} 
                  color="bg-amber-500"
                />
                <SentimentBar 
                  label="Negative" 
                  count={articles.filter(a => a.sentiment === "negative").length} 
                  total={articles.length} 
                  color="bg-rose-500"
                />
              </div>
            </div>
            <PieChart className="absolute -bottom-4 -right-4 h-24 w-24 text-primary/5 rotate-12" />
          </div>

          {/* Trending Movers */}
          <div className="card-surface p-5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-lg bg-orange-500/10 text-orange-500">
                  <Flame className="h-5 w-5" />
                </div>
                <h4 className="font-bold text-sm">Top Movers</h4>
              </div>
              <Link href="/markets" className="text-[10px] uppercase font-bold text-primary hover:underline">View All</Link>
            </div>
            
            <div className="space-y-3">
              {sidebarLoading ? (
                Array.from({ length: 4 }).map((_, i) => <div key={i} className="skeleton h-12 w-full rounded-xl" />)
              ) : overview?.topGainers.slice(0, 5).map((stock) => (
                <MoverItem key={stock.symbol} stock={stock} />
              ))}
            </div>
          </div>

          {/* Sector Heatmap */}
          <div className="card-surface p-5">
            <div className="flex items-center gap-2 mb-4">
              <div className="p-2 rounded-lg bg-blue-500/10 text-blue-500">
                <PieChart className="h-5 w-5" />
              </div>
              <h4 className="font-bold text-sm">Sector Trends</h4>
            </div>
            <div className="grid grid-cols-2 gap-2">
              {sidebarLoading ? (
                Array.from({ length: 4 }).map((_, i) => <div key={i} className="skeleton h-14 w-full rounded-xl" />)
              ) : overview?.sectorHeatmap.slice(0, 4).map((sector) => (
                <SectorMiniCard key={sector.sector} sector={sector} />
              ))}
            </div>
          </div>

        </aside>
      </div>
    </div>
  );
}

function SentimentBar({ label, count, total, color }: { label: string; count: number; total: number; color: string }) {
  const pct = total > 0 ? (count / total) * 100 : 0;
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-[10px] font-bold">
        <span className="text-muted-foreground">{label}</span>
        <span>{count}</span>
      </div>
      <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden">
        <div 
          className={cn("h-full rounded-full transition-all duration-1000", color)} 
          style={{ width: `${pct}%` }} 
        />
      </div>
    </div>
  );
}

function MoverItem({ stock }: { stock: MarketMover }) {
  const isUp = stock.changePct >= 0;
  return (
    <Link 
      href={`/markets/${stock.displaySymbol}`}
      className="flex items-center justify-between p-2.5 rounded-xl hover:bg-muted/50 border border-transparent hover:border-border transition-all"
    >
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-background flex items-center justify-center font-bold text-[10px] border border-border">
          {stock.displaySymbol.slice(0, 2)}
        </div>
        <div>
          <div className="text-xs font-bold">{stock.displaySymbol}</div>
          <div className="text-[10px] text-muted-foreground line-clamp-1">{stock.companyName}</div>
        </div>
      </div>
      <div className="text-right">
        <div className="text-xs font-bold">{formatPercent(stock.changePct)}</div>
        <div className={cn("flex items-center justify-end text-[10px]", isUp ? "text-emerald-500" : "text-rose-500")}>
          {isUp ? <ArrowUpRight className="h-2.5 w-2.5" /> : <ArrowDownRight className="h-2.5 w-2.5" />}
        </div>
      </div>
    </Link>
  );
}

function SectorMiniCard({ sector }: { sector: SectorHeatmapCell }) {
  const isUp = sector.changePct >= 0;
  return (
    <div className={cn(
      "p-2.5 rounded-xl border flex flex-col justify-between h-16",
      isUp ? "bg-emerald-500/5 border-emerald-500/10" : "bg-rose-500/5 border-rose-500/10"
    )}>
      <div className="text-[10px] font-bold text-muted-foreground line-clamp-1 uppercase tracking-tighter">
        {sector.sector}
      </div>
      <div className={cn("text-xs font-black", isUp ? "text-emerald-500" : "text-rose-500")}>
        {formatPercent(sector.changePct)}
      </div>
    </div>
  );
}
