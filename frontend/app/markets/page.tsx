"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Bell, Flame, LayoutGrid, Loader2, Radio, Zap, TrendingUp, TrendingDown, Activity, Home, Star } from "lucide-react";
import { useAuth } from "@clerk/nextjs";
import { toast } from "sonner";
import { MarketDisabledState } from "@/components/markets/market-disabled-state";
import { MarketNewsCard } from "@/components/markets/market-news-card";
import { MarketSearch } from "@/components/markets/market-search";
import { useMarketSocket } from "@/hooks/use-market-socket";
import { marketsApi } from "@/lib/api/client";
import { marketsFeatureEnabled } from "@/lib/markets/feature-flag";
import { mergeArticleBookmarks, useMarketPulseStore } from "@/lib/markets/store";
import type { EnrichedNewsArticle, MarketOverviewResponse, SearchContextResponse } from "@/lib/markets/types";
import { cn, formatCurrency, formatPercent, formatLargeNumber } from "@/lib/utils";

export default function MarketsPage() {
  const { isLoaded: authLoaded, userId } = useAuth();
  const [overview, setOverview] = useState<MarketOverviewResponse | null>(null);
  const [context, setContext] = useState<SearchContextResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [newsError, setNewsError] = useState<string | null>(null);
  const [newsPage, setNewsPage] = useState(1);
  const [news, setNews] = useState<EnrichedNewsArticle[]>([]);
  const newsFilters = useMarketPulseStore((state) => state.newsFilters);
  const updateNewsFilters = useMarketPulseStore((state) => state.updateNewsFilters);
  const watchlistSymbols = useMarketPulseStore((state) => state.watchlistSymbols);
  const setWatchlistSymbols = useMarketPulseStore((state) => state.setWatchlistSymbols);
  const bookmarkedUrls = useMarketPulseStore((state) => state.bookmarkedUrls);
  const setBookmarkedUrls = useMarketPulseStore((state) => state.setBookmarkedUrls);
  const toggleBookmark = useMarketPulseStore((state) => state.toggleBookmark);
  const setBreakingNewsCount = useMarketPulseStore((state) => state.setBreakingNewsCount);
  const setMarketStatus = useMarketPulseStore((state) => state.setMarketStatus);
  const liveQuotes = useMarketPulseStore((state) => state.liveQuotes);
  const socketStatus = useMarketPulseStore((state) => state.socketStatus);

  useMarketSocket(
    useMemo(() => {
      const symbols = new Set<string>(watchlistSymbols);
      overview?.topGainers.slice(0, 3).forEach((item) => symbols.add(item.displaySymbol));
      overview?.topLosers.slice(0, 2).forEach((item) => symbols.add(item.displaySymbol));
      return Array.from(symbols);
    }, [overview?.topGainers, overview?.topLosers, watchlistSymbols])
  );

  useEffect(() => {
    if (!marketsFeatureEnabled) return;
    let active = true;
    const loadCore = async () => {
      try {
        setLoading(true);
        setLoadError(null);
        const [overviewResponse, contextResponse] = await Promise.all([
          marketsApi.overview(),
          marketsApi.searchContext(),
        ]);
        if (!active) return;
        setOverview(overviewResponse.data);
        setContext(contextResponse.data);
        setBreakingNewsCount(overviewResponse.data.breakingNewsCount);
        setMarketStatus(overviewResponse.data.marketStatus);
      } catch {
        if (!active) return;
        setLoadError("Market Pulse is having trouble reaching live data right now.");
        toast.error("Market Pulse could not load");
      } finally {
        if (active) setLoading(false);
      }
    };
    loadCore();
    return () => {
      active = false;
    };
  }, [setBreakingNewsCount, setMarketStatus]);

  useEffect(() => {
    if (!marketsFeatureEnabled || !authLoaded) return;
    let active = true;

    const loadPersonalization = async () => {
      if (!userId) {
        if (!active) return;
        setWatchlistSymbols([]);
        setBookmarkedUrls([]);
        return;
      }

      const [watchlistResult, bookmarkResult] = await Promise.allSettled([
        marketsApi.watchlist(),
        marketsApi.bookmarks(),
      ]);

      if (!active) return;

      if (watchlistResult.status === "fulfilled") {
        setWatchlistSymbols(
          watchlistResult.value.data.map((item: { displaySymbol: string }) => item.displaySymbol)
        );
      } else {
        setWatchlistSymbols([]);
      }

      if (bookmarkResult.status === "fulfilled") {
        setBookmarkedUrls(
          bookmarkResult.value.data.map((item: { source_url: string }) => item.source_url)
        );
      } else {
        setBookmarkedUrls([]);
      }
    };

    loadPersonalization();
    return () => {
      active = false;
    };
  }, [authLoaded, setBookmarkedUrls, setWatchlistSymbols, userId]);

  useEffect(() => {
    if (!marketsFeatureEnabled) return;
    let active = true;
    const loadNews = async () => {
      try {
        setNewsError(null);
        const response = await marketsApi.news({
          page: newsPage,
          limit: 12,
          category: newsFilters.category !== "all" ? newsFilters.category : undefined,
          exchange: newsFilters.exchange !== "all" ? newsFilters.exchange : undefined,
          sector: newsFilters.sector !== "all" ? newsFilters.sector : undefined,
          marketCap: newsFilters.marketCap !== "all" ? newsFilters.marketCap : undefined,
          sentiment: newsFilters.sentiment !== "all" ? newsFilters.sentiment : undefined,
        });
        if (!active) return;
        setNews(mergeArticleBookmarks(response.data.articles, bookmarkedUrls));
      } catch {
        if (!active) return;
        setNewsError("Live market news could not refresh. Showing the last available state.");
        toast.error("Unable to refresh the market news feed");
      }
    };
    loadNews();
    return () => {
      active = false;
    };
  }, [bookmarkedUrls, newsFilters.category, newsFilters.exchange, newsFilters.marketCap, newsFilters.sector, newsFilters.sentiment, newsPage]);

  if (!marketsFeatureEnabled) {
    return <MarketDisabledState />;
  }

  const watchlistView = (overview?.watchlist ?? []).map((item) => liveQuotes[item.displaySymbol] ?? item);

  const toggleBookmarkRemote = async (article: EnrichedNewsArticle) => {
    try {
      toggleBookmark(article.sourceUrl);
      if (bookmarkedUrls.includes(article.sourceUrl)) {
        await marketsApi.deleteBookmark(article.id);
      } else {
        await marketsApi.addBookmark({
          articleId: article.id,
          title: article.title,
          sourceUrl: article.sourceUrl,
          source: article.source,
          publishedAt: article.publishedAt,
        });
      }
    } catch {
      toggleBookmark(article.sourceUrl);
      toast.error("Bookmark action failed");
    }
  };

  return (
    <div className="market-shell space-y-8 rounded-[28px] p-4 md:p-8">
      {/* ── Breadcrumbs ── */}
      <nav className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">
        <Link href="/dashboard" className="flex items-center gap-1.5 transition hover:text-white">
          <Home className="h-3 w-3" />
          Dashboard
        </Link>
        <span className="text-slate-800">/</span>
        <span className="text-slate-300">Market Pulse</span>
      </nav>

      <section className="animate-in fade-in slide-in-from-top-4 duration-700">
        <div className="flex flex-col gap-8 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-4xl space-y-4">
            <div className="flex flex-wrap items-center gap-3">
              <span className={cn(
                "market-pill flex items-center gap-2 px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider",
                overview?.marketStatus === "live" ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-400" : "text-slate-500"
              )}>
                <Radio className={cn("h-3 w-3", overview?.marketStatus === "live" && "animate-pulse")} />
                {overview?.marketStatus ?? "Connecting..."}
              </span>
              <span className="market-pill flex items-center gap-2 px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                <Zap className="h-3 w-3 text-amber-400" />
                Live {socketStatus}
              </span>
            </div>
            <h1 className="text-5xl font-bold tracking-tight text-white md:text-7xl">
              India-first stock <span className="text-emerald-400">intelligence.</span>
            </h1>
            <p className="max-w-2xl text-lg leading-relaxed text-slate-400">
              Real-time pricing, AI-powered news transmission analysis, and institutional-grade market benchmarks.
            </p>
          </div>

          <div className="flex items-center gap-4">
            <div className="market-card flex items-center gap-5 p-4 pr-6">
              <div className="relative flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-400">
                <Bell className="h-7 w-7" />
                {(overview?.breakingNewsCount ?? 0) > 0 && (
                  <span className="absolute right-3.5 top-3.5 h-3 w-3 animate-ping rounded-full bg-emerald-500" />
                )}
              </div>
              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Breaking</p>
                <p className="mt-1 text-3xl font-bold text-white">{overview?.breakingNewsCount ?? 0}</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="animate-in fade-in slide-in-from-bottom-4 duration-700 delay-200">
        <MarketSearch context={context} />
      </div>

      {loadError && !overview && !loading ? (
        <section className="market-card p-5 md:p-6">
          <p className="market-eyebrow">Connection Issue</p>
          <h2 className="mt-2 text-2xl font-semibold text-white">Market Pulse is temporarily unavailable</h2>
          <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-300">{loadError}</p>
          <button onClick={() => window.location.reload()} className="btn-primary mt-5">
            Retry module
          </button>
        </section>
      ) : null}

      {loading || !overview ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 8 }).map((_, index) => (
            <div key={index} className="market-card h-40 animate-pulse bg-white/5" />
          ))}
        </div>
      ) : (
        <div className="space-y-8 animate-in fade-in duration-1000 delay-300">
          <section className="grid gap-6 xl:grid-cols-[1.8fr,0.9fr]">
            <div className="market-card p-6 md:p-8">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Activity className="h-5 w-5 text-emerald-400" />
                  <h2 className="text-xl font-bold text-white uppercase tracking-wider">Benchmark Indices</h2>
                </div>
                <div className="market-pill text-[10px] font-bold px-3 py-1">REAL-TIME</div>
              </div>
              <div className="mt-8 grid gap-4 md:grid-cols-3">
                {overview.indices.map((item) => (
                  <div key={item.label} className="group relative rounded-3xl border border-white/[0.06] bg-white/[0.02] p-6 transition-all hover:bg-white/[0.04]">
                    <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">{item.label}</p>
                    <p className="mt-4 text-3xl font-bold tracking-tight text-white group-hover:text-emerald-400 transition-colors">
                      {item.value.toLocaleString("en-IN", { maximumFractionDigits: 2 })}
                    </p>
                    <div className={cn(
                      "mt-2 flex items-center gap-1 text-sm font-bold",
                      item.changePct >= 0 ? "text-emerald-400" : "text-rose-400"
                    )}>
                      {item.changePct >= 0 ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                      {formatPercent(item.changePct)}
                    </div>
                    <div className="mt-6 flex h-12 items-end gap-1.5 opacity-60 group-hover:opacity-100 transition-opacity">
                      {item.sparkline.map((point, index) => (
                        <span
                          key={`${item.label}-${index}`}
                          className={cn("w-full rounded-t-sm", item.changePct >= 0 ? "bg-emerald-500/40" : "bg-rose-500/40")}
                          style={{ height: `${Math.max(20, (point / Math.max(...item.sparkline)) * 100)}%` }}
                        />
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="market-card p-6 md:p-8">
              <div className="flex items-center gap-3">
                <Star className="h-5 w-5 text-amber-400" />
                <h2 className="text-xl font-bold text-white uppercase tracking-wider">Your Watchlist</h2>
              </div>
              <div className="mt-8 space-y-4">
                {watchlistView.length ? watchlistView.map((item) => (
                  <Link key={item.displaySymbol} href={`/markets/${item.displaySymbol}`} className="market-inline-row group p-4 bg-white/[0.02] rounded-2xl border border-white/[0.04] transition hover:bg-white/[0.05] hover:border-emerald-500/20">
                    <div>
                      <p className="font-bold text-white group-hover:text-emerald-400 transition">{item.displaySymbol}</p>
                      <p className="text-[10px] font-medium text-slate-500 uppercase tracking-wider">{item.companyName.slice(0, 24)}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-white">{formatCurrency(item.currentPrice)}</p>
                      <p className={cn("text-[11px] font-bold", item.changePct >= 0 ? "text-emerald-400" : "text-rose-400")}>
                        {item.changePct >= 0 ? "+" : ""}{formatPercent(item.changePct)}
                      </p>
                    </div>
                  </Link>
                )) : (
                  <div className="rounded-2xl border border-dashed border-white/10 p-8 text-center">
                    <p className="text-sm text-slate-500 italic leading-relaxed">
                      Your watchlist is empty. Add symbols from any company detail page.
                    </p>
                  </div>
                )}
              </div>
            </div>
          </section>

          <section className="grid gap-6 xl:grid-cols-[1fr,1fr,1fr]">
            <MoverCard title="Momentum Leaders" movers={overview.topGainers} type="gainers" liveQuotes={liveQuotes} />
            <MoverCard title="Pressure Pockets" movers={overview.topLosers} type="losers" liveQuotes={liveQuotes} />
            <MoverCard title="Volume Heavy" movers={overview.mostActive} type="active" liveQuotes={liveQuotes} />
          </section>

          <section className="grid gap-6 xl:grid-cols-[1.3fr,0.85fr,0.85fr]">
            <div className="market-card p-6 md:p-8">
              <div className="flex items-center justify-between mb-8">
                <div className="flex items-center gap-3">
                  <LayoutGrid className="h-5 w-5 text-slate-400" />
                  <h2 className="text-xl font-bold text-white uppercase tracking-wider">Sector Heatmap</h2>
                </div>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                {overview.sectorHeatmap.map((cell) => (
                  <div
                    key={cell.sector}
                    className="relative overflow-hidden rounded-3xl border border-white/5 p-6 group transition-all hover:scale-[1.02]"
                    style={{
                      background:
                        cell.changePct >= 0
                          ? `linear-gradient(135deg, rgba(16,185,129,${Math.min(0.2, Math.abs(cell.changePct) / 5)}) 0%, rgba(8,16,24,1) 100%)`
                          : `linear-gradient(135deg, rgba(239,68,68,${Math.min(0.2, Math.abs(cell.changePct) / 5)}) 0%, rgba(8,16,24,1) 100%)`,
                    }}
                  >
                    <p className="text-sm font-bold text-white">{cell.sector}</p>
                    <p className={cn("mt-4 text-3xl font-bold", cell.changePct >= 0 ? "text-emerald-400" : "text-rose-400")}>
                      {cell.changePct >= 0 ? "+" : ""}{formatPercent(cell.changePct)}
                    </p>
                    <div className="mt-4 flex flex-wrap gap-1.5">
                      {cell.leaders.map(leader => (
                        <span key={leader} className="text-[9px] font-bold uppercase tracking-widest text-slate-500 bg-white/5 px-2 py-0.5 rounded-md">
                          {leader}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="market-card p-6 md:p-8">
              <h3 className="text-sm font-bold uppercase tracking-[0.2em] text-slate-500 mb-8">Flow Monitor</h3>
              <div className="space-y-8">
                <FlowBar label="FII Net Flow" value={overview.fiiDiiActivity.fiiNet} />
                <FlowBar label="DII Net Flow" value={overview.fiiDiiActivity.diiNet} />
                <div className="rounded-2xl bg-white/[0.03] p-4 text-[11px] text-slate-500 leading-relaxed italic border border-white/[0.05]">
                  Exchange provided data as of {overview.fiiDiiActivity.sessionDate}. Values in Cr.
                </div>
              </div>
            </div>

            <div className="market-card p-6 md:p-8">
              <h3 className="text-sm font-bold uppercase tracking-[0.2em] text-slate-500 mb-8">Primary Market</h3>
              <div className="space-y-4">
                {overview.ipoTracker.map((item) => (
                  <div key={item.id} className="group rounded-2xl border border-white/[0.06] bg-white/[0.02] p-5 transition hover:bg-white/[0.04]">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="font-bold text-white group-hover:text-emerald-400 transition">{item.name}</p>
                        <p className="mt-1 text-[10px] font-bold text-slate-500 uppercase tracking-wider">{item.status} · {item.exchange}</p>
                      </div>
                      <span className="rounded-lg bg-emerald-500/10 px-2 py-1 text-[10px] font-bold text-emerald-400">
                        {item.gmp ?? 0}% GMP
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>

          <section className="grid gap-6 xl:grid-cols-[1.6fr,0.9fr]">
            <div className="market-card p-6 md:p-8">
              <div className="flex flex-wrap items-center justify-between gap-6 mb-10">
                <div className="flex items-center gap-3">
                  <Activity className="h-5 w-5 text-emerald-400" />
                  <h2 className="text-xl font-bold text-white uppercase tracking-wider">AI Transmission Feed</h2>
                </div>
                <div className="flex flex-wrap gap-2">
                  {[
                    { key: "category", value: "market_analysis", label: "Analysis" },
                    { key: "sentiment", value: "bullish", label: "Bullish" },
                    { key: "exchange", value: "NSE", label: "NSE" },
                  ].map((filter) => (
                    <button
                      key={filter.label}
                      onClick={() =>
                        updateNewsFilters({
                          [filter.key]:
                            newsFilters[filter.key as keyof typeof newsFilters] === filter.value ? "all" : filter.value,
                        })
                      }
                      className={cn(
                        "rounded-full border px-4 py-1.5 text-[11px] font-bold uppercase tracking-wider transition-all",
                        newsFilters[filter.key as keyof typeof newsFilters] === filter.value
                          ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
                          : "border-white/10 bg-white/5 text-slate-400 hover:text-white"
                      )}
                    >
                      {filter.label}
                    </button>
                  ))}
                </div>
              </div>
              <div className="space-y-6">
                {news.length ? news.map((article) => (
                  <MarketNewsCard key={article.id} article={article} onToggleBookmark={toggleBookmarkRemote} />
                )) : (
                  <div className="flex items-center justify-center py-20 bg-white/[0.02] rounded-3xl border border-dashed border-white/10">
                    <Loader2 className="h-6 w-6 animate-spin text-emerald-500" />
                  </div>
                )}
              </div>
            </div>

            <div className="space-y-6">
              <div className="market-card p-6 md:p-8">
                <h3 className="text-sm font-bold uppercase tracking-[0.2em] text-slate-500 mb-8">Macro Catalysts</h3>
                <div className="space-y-5">
                  {overview.economicCalendar.map((event) => (
                    <div key={event.id} className="relative pl-6 before:absolute before:left-0 before:top-1.5 before:h-2 before:w-2 before:rounded-full before:bg-emerald-500">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="text-sm font-bold text-white">{event.title}</p>
                          <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mt-1">{event.category}</p>
                        </div>
                        <span className={cn(
                          "rounded-lg px-2 py-1 text-[9px] font-bold uppercase tracking-widest",
                          event.impact === "high" ? "bg-rose-500/10 text-rose-400" : "bg-white/5 text-slate-400"
                        )}>
                          {event.impact}
                        </span>
                      </div>
                      <p className="mt-2 text-[10px] font-medium text-slate-500">
                        {new Date(event.scheduledAt).toLocaleString("en-IN", {
                          dateStyle: "medium",
                          timeStyle: "short",
                        })}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="market-card p-6 md:p-8">
                <h3 className="text-sm font-bold uppercase tracking-[0.2em] text-slate-500 mb-8">System Signals</h3>
                <div className="grid gap-3">
                  <SignalTile label="Coverage" value={watchlistSymbols.length.toString()} detail="Active Watchlist" />
                  <SignalTile label="Saved" value={bookmarkedUrls.length.toString()} detail="Knowledge Base" />
                  <SignalTile label="Volatility" value={`${overview.latestNews.length ? Math.max(...overview.latestNews.map((item) => item.impactScore)) : 0}/100`} detail="Transmission Risk" />
                </div>
              </div>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}

function MoverCard({ title, movers, type, liveQuotes }: { title: string, movers: any[], type: string, liveQuotes: any }) {
  const Icon = type === "gainers" ? TrendingUp : type === "losers" ? TrendingDown : Activity;
  const color = type === "gainers" ? "text-emerald-400" : type === "losers" ? "text-rose-400" : "text-amber-400";

  return (
    <div className="market-card p-6 md:p-8">
      <div className="flex items-center gap-3 mb-8">
        <Icon className={cn("h-4 w-4", color)} />
        <h3 className="text-sm font-bold uppercase tracking-[0.2em] text-slate-500">{title}</h3>
      </div>
      <div className="space-y-4">
        {movers.slice(0, 5).map((item) => {
          const live = liveQuotes[item.displaySymbol] ?? item;
          return (
            <Link key={item.displaySymbol} href={`/markets/${item.displaySymbol}`} className="market-inline-row group">
              <div>
                <p className="font-bold text-white transition group-hover:text-emerald-400">{item.displaySymbol}</p>
                <p className="text-[10px] font-medium text-slate-500 uppercase tracking-wider">{item.sector}</p>
              </div>
              <div className="text-right">
                <p className="font-semibold text-white">{formatCurrency(live.currentPrice)}</p>
                <p className={cn("text-[11px] font-bold", live.changePct >= 0 ? "text-emerald-400" : "text-rose-400")}>
                  {live.changePct >= 0 ? "+" : ""}{formatPercent(live.changePct)}
                </p>
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}

function FlowBar({ label, value }: { label: string; value: number }) {
  const positive = value >= 0;
  const width = Math.min(100, Math.max(18, Math.abs(value) / 35));
  return (
    <div>
      <div className="flex items-center justify-between text-sm text-white">
        <span>{label}</span>
        <span className={positive ? "text-emerald-300" : "text-rose-300"}>
          {formatLargeNumber(value)}
        </span>
      </div>
      <div className="mt-2 h-2 rounded-full bg-white/[0.06]">
        <div
          className={cn("h-2 rounded-full", positive ? "bg-emerald-400" : "bg-rose-400")}
          style={{ width: `${width}%` }}
        />
      </div>
    </div>
  );
}

function SignalTile({ label, value, detail }: { label: string; value: string; detail: string }) {
  return (
    <div className="rounded-2xl border border-white/[0.08] bg-black/20 p-4">
      <p className="text-[11px] uppercase tracking-[0.24em] text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-white">{value}</p>
      <p className="mt-1 text-xs text-slate-400">{detail}</p>
    </div>
  );
}

function TrendingUpBadge() {
  return (
    <div className="rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-1 text-xs text-emerald-200">
      Momentum
    </div>
  );
}
