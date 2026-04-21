"use client";

import { useEffect, useState } from "react";
import { newsApi } from "@/lib/api/client";
import { ExternalLink, TrendingUp, TrendingDown, Minus, Newspaper, Search, X } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { toast } from "sonner";

interface Article {
  id: string; ticker: string | null; title: string;
  description?: string; summary?: string; url: string; source: string;
  published_at: string;
  sentiment: "positive" | "negative" | "neutral";
  sentiment_score: number; category: string; image_url: string | null;
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
  positive: { icon: TrendingUp,   color: "#22C55E", badge: "badge-green",  label: "Positive" },
  negative: { icon: TrendingDown, color: "#EF4444", badge: "badge-red",    label: "Negative" },
  neutral:  { icon: Minus,        color: "#f59e0b", badge: "badge-amber",  label: "Neutral"  },
};

function ArticleThumbnail({ src, alt }: { src: string; alt: string }) {
  const [hidden, setHidden] = useState(false);

  if (!src || hidden) {
    return null;
  }

  return (
    <div className="w-20 h-14 relative rounded-xl overflow-hidden flex-shrink-0 hidden sm:block">
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
  const [articles,     setArticles]     = useState<Article[]>([]);
  const [loading,      setLoading]      = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [totalCount,   setTotalCount]   = useState(0);
  const [filters, setFilters] = useState<FilterState>({
    ticker: "",
    category: "all",
    sentiment: "all",
    timeRange: "all",
  });
  const [inputVal,     setInputVal]     = useState("");

  useEffect(() => {
    fetchNews(filters);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const fetchNews = async (activeFilters: FilterState) => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const params: {
        page: number;
        limit: number;
        ticker?: string;
        category?: string;
        sentiment?: string;
        time_range?: "1h" | "6h" | "24h" | "7d" | "30d";
      } = {
        page: 1,
        limit: 30,
      };

      if (activeFilters.ticker) params.ticker = activeFilters.ticker;
      if (activeFilters.category !== "all") params.category = activeFilters.category;
      if (activeFilters.sentiment !== "all") params.sentiment = activeFilters.sentiment;
      if (activeFilters.timeRange !== "all") params.time_range = activeFilters.timeRange;

      const res = await newsApi.list(params);
      const payload = res.data as NewsListResponse;
      setArticles(payload.articles ?? []);
      setTotalCount(payload.total ?? payload.articles?.length ?? 0);
    } catch (error: any) {
      const status = error?.response?.status;
      setArticles([]);
      setTotalCount(0);

      if (status === 503) {
        setErrorMessage("News providers are temporarily unavailable. Please try again in a few minutes.");
        toast.error("News providers are temporarily unavailable. Please try again in a few minutes.");
      } else if (status) {
        setErrorMessage(`Failed to load news (HTTP ${status}).`);
        toast.error(`Failed to load news (HTTP ${status})`);
      } else {
        setErrorMessage("Failed to reach the backend news service.");
        toast.error("Failed to load news (backend unreachable)");
      }
      console.error("News fetch failed", error);
    } finally {
      setLoading(false);
    }
  };

  const handleFilter = () => {
    const next = { ...filters, ticker: inputVal.trim().toUpperCase() };
    setFilters(next);
    fetchNews(next);
  };

  const handleClear = () => {
    setInputVal("");
    const next: FilterState = {
      ticker: "",
      category: "all",
      sentiment: "all",
      timeRange: "all",
    };
    setFilters(next);
    fetchNews(next);
  };

  const updateFilter = <K extends keyof FilterState>(key: K, value: FilterState[K]) => {
    const next = { ...filters, [key]: value };
    setFilters(next);
    fetchNews(next);
  };

  return (
    <div className="max-w-4xl">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-page-title">Market News</h1>
          <p className="text-body-sm text-muted-foreground mt-0.5">
            Real-time news with AI sentiment analysis
          </p>
        </div>
        {!loading && (
          <span className="badge badge-primary mt-1">
            {totalCount} articles
          </span>
        )}
      </div>

      {/* Filter bar */}
      <div className="card-surface p-4 mb-5 animate-slide-in-up">
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
            <input
              value={inputVal}
              onChange={(e) => setInputVal(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleFilter()}
              placeholder="Filter by ticker (RELIANCE, INFY…)"
              className="input-field pl-10 pr-10"
            />
            {inputVal && (
              <button
                onClick={handleClear}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>
          <button onClick={handleFilter} className="btn-primary px-4">
            Apply
          </button>
          <button onClick={handleClear} className="btn-secondary px-4">
            Reset
          </button>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 mt-3">
          <select
            value={filters.category}
            onChange={(e) => updateFilter("category", e.target.value as CategoryFilter)}
            className="input-field"
          >
            <option value="all">All Categories</option>
            <option value="general">General</option>
            <option value="earnings">Earnings</option>
            <option value="merger">Merger</option>
            <option value="macro">Macro</option>
            <option value="regulatory">Regulatory</option>
            <option value="market_analysis">Market Analysis</option>
          </select>
          <select
            value={filters.sentiment}
            onChange={(e) => updateFilter("sentiment", e.target.value as SentimentFilter)}
            className="input-field"
          >
            <option value="all">All Sentiments</option>
            <option value="positive">Positive</option>
            <option value="neutral">Neutral</option>
            <option value="negative">Negative</option>
          </select>
          <select
            value={filters.timeRange}
            onChange={(e) => updateFilter("timeRange", e.target.value as TimeRange)}
            className="input-field"
          >
            <option value="all">All Time</option>
            <option value="1h">Last 1 hour</option>
            <option value="6h">Last 6 hours</option>
            <option value="24h">Last 24 hours</option>
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
          </select>
        </div>
        {(filters.ticker || filters.category !== "all" || filters.sentiment !== "all" || filters.timeRange !== "all") && (
          <p className="text-label-xs text-muted-foreground mt-2">
            Filters:
            {filters.ticker ? ` ticker=${filters.ticker}` : ""}{" "}
            {filters.category !== "all" ? ` category=${filters.category}` : ""}{" "}
            {filters.sentiment !== "all" ? ` sentiment=${filters.sentiment}` : ""}{" "}
            {filters.timeRange !== "all" ? ` range=${filters.timeRange}` : ""}
          </p>
        )}
      </div>

      {/* Content */}
      {loading ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="card-surface p-4">
              <div className="flex gap-3">
                <div className="skeleton rounded-xl w-20 h-14 hidden sm:block flex-shrink-0" />
                <div className="flex-1 space-y-2">
                  <div className="skeleton h-3 w-32 rounded" />
                  <div className="skeleton h-4 w-full rounded" />
                  <div className="skeleton h-3 w-3/4 rounded" />
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : errorMessage ? (
        <div className="text-center py-20 animate-fade-in">
          <div
            className="kpi-icon-circle mx-auto mb-4"
            style={{ background: "hsl(var(--destructive) / 0.08)", width: "64px", height: "64px" }}
          >
            <Newspaper className="h-7 w-7 opacity-50" style={{ color: "hsl(var(--destructive))" }} />
          </div>
          <p className="text-card-title text-foreground">News service unavailable</p>
          <p className="text-body-sm text-muted-foreground mt-1">{errorMessage}</p>
        </div>
      ) : articles.length === 0 ? (
        <div className="text-center py-20 animate-fade-in">
          <div
            className="kpi-icon-circle mx-auto mb-4"
            style={{ background: "hsl(var(--primary) / 0.08)", width: "64px", height: "64px" }}
          >
            <Newspaper className="h-7 w-7 opacity-40" style={{ color: "hsl(var(--primary))" }} />
          </div>
          <p className="text-card-title text-muted-foreground">No news found</p>
        </div>
      ) : (
        <div className="space-y-3">
          {articles.map((a, i) => {
            const cfg = sentimentConfig[a.sentiment];
            const SentIcon = cfg.icon;
            const previewText = a.description ?? a.summary ?? "";
            return (
              <a
                key={a.id}
                href={a.url}
                target="_blank"
                rel="noopener noreferrer"
                className={`block card-surface p-4 group overflow-hidden animate-slide-in-up`}
                style={{
                  borderLeft: `3px solid ${cfg.color}`,
                  animationDelay: `${Math.min(i * 40, 400)}ms`,
                }}
              >
                <div className="flex items-start gap-3">
                  {a.image_url && (
                    <ArticleThumbnail src={a.image_url} alt={a.title} />
                  )}
                  <div className="flex-1 min-w-0">
                    {/* Meta row */}
                    <div className="flex flex-wrap items-center gap-1.5 mb-2">
                      {a.ticker && (
                        <span className="badge badge-primary">{a.ticker}</span>
                      )}
                      <span className="badge bg-muted text-muted-foreground capitalize">
                        {a.category.replace("_", " ")}
                      </span>
                      <div className={`badge ml-auto ${cfg.badge}`}>
                        <SentIcon className="h-3 w-3" />
                        {cfg.label}
                        <span className="opacity-70">
                          {a.sentiment_score > 0 ? "+" : ""}{a.sentiment_score.toFixed(2)}
                        </span>
                      </div>
                    </div>

                    {/* Title */}
                    <h3 className="text-card-title leading-snug group-hover:text-primary transition-colors line-clamp-2 mb-1">
                      {a.title}
                    </h3>

                    {/* Summary */}
                    {previewText && (
                      <p className="text-label-xs text-muted-foreground line-clamp-2 mb-2">
                        {previewText}
                      </p>
                    )}

                    {/* Footer */}
                    <div className="flex items-center gap-2 text-label-xs text-muted-foreground">
                      <span className="font-medium">{a.source}</span>
                      <span>·</span>
                      <span>{formatDistanceToNow(new Date(a.published_at), { addSuffix: true })}</span>
                      <ExternalLink className="h-3 w-3 ml-auto opacity-0 group-hover:opacity-60 transition-opacity" />
                    </div>
                  </div>
                </div>
              </a>
            );
          })}
        </div>
      )}
    </div>
  );
}
