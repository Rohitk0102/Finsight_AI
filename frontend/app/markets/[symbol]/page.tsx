"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import * as Tabs from "@radix-ui/react-tabs";
import { BellRing, CandlestickChart, Home, LineChart as LineChartIcon, Star, CheckCircle2, ArrowLeft } from "lucide-react";
import { Pie, PieChart, ResponsiveContainer, Cell, Tooltip as RechartsTooltip } from "recharts";
import { toast } from "sonner";
import { MarketChart } from "@/components/markets/market-chart";
import { MarketDisabledState } from "@/components/markets/market-disabled-state";
import { MarketNewsCard } from "@/components/markets/market-news-card";
import { useMarketSocket } from "@/hooks/use-market-socket";
import { marketsApi } from "@/lib/api/client";
import { marketsFeatureEnabled } from "@/lib/markets/feature-flag";
import { useMarketPulseStore } from "@/lib/markets/store";
import type { ChartRange, CompanyChartResponse, CompanyDetailResponse, EnrichedNewsArticle, IndicatorKey, PriceAlert } from "@/lib/markets/types";
import { cn, formatCurrency, formatLargeNumber, formatPercent } from "@/lib/utils";

const ranges: ChartRange[] = ["1D", "1W", "1M", "3M", "6M", "1Y", "5Y"];
const indicators: IndicatorKey[] = ["SMA", "EMA", "RSI", "MACD", "Bollinger"];

export default function MarketCompanyPage() {
  const { isLoaded: authLoaded, userId } = useAuth();
  const params = useParams<{ symbol: string }>();
  const symbol = (params?.symbol ?? "").toUpperCase();
  const [detail, setDetail] = useState<CompanyDetailResponse | null>(null);
  const [chart, setChart] = useState<CompanyChartResponse | null>(null);
  const [news, setNews] = useState<EnrichedNewsArticle[]>([]);
  const [alerts, setAlerts] = useState<PriceAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [alertType, setAlertType] = useState<"price_above" | "price_below" | "pct_change">("price_above");
  const [thresholdValue, setThresholdValue] = useState("");
  const chartRange = useMarketPulseStore((state) => state.chartRange);
  const chartMode = useMarketPulseStore((state) => state.chartMode);
  const setChartRange = useMarketPulseStore((state) => state.setChartRange);
  const setChartMode = useMarketPulseStore((state) => state.setChartMode);
  const selectedIndicators = useMarketPulseStore((state) => state.indicators);
  const toggleIndicator = useMarketPulseStore((state) => state.toggleIndicator);
  const watchlistSymbols = useMarketPulseStore((state) => state.watchlistSymbols);
  const toggleWatchlistSymbol = useMarketPulseStore((state) => state.toggleWatchlistSymbol);
  const bookmarkedUrls = useMarketPulseStore((state) => state.bookmarkedUrls);
  const toggleBookmark = useMarketPulseStore((state) => state.toggleBookmark);
  const rememberViewed = useMarketPulseStore((state) => state.rememberViewed);
  const liveQuotes = useMarketPulseStore((state) => state.liveQuotes);

  useMarketSocket(symbol ? [symbol] : []);

  useEffect(() => {
    if (!marketsFeatureEnabled || !symbol) return;
    rememberViewed(symbol);
    let active = true;
    const load = async () => {
      try {
        setLoading(true);
        setLoadError(null);
        const [detailResponse, chartResponse, newsResponse, alertsResponse] = await Promise.all([
          marketsApi.company(symbol),
          marketsApi.companyChart(symbol, chartRange),
          marketsApi.companyNews(symbol),
          authLoaded && userId ? marketsApi.alerts() : Promise.resolve({ data: [] }),
        ]);
        if (!active) return;
        setDetail(detailResponse.data);
        setChart(chartResponse.data);
        setNews(newsResponse.data);
        setAlerts(alertsResponse.data.filter((item: PriceAlert) => item.symbol === symbol));
      } catch {
        if (!active) return;
        setLoadError("This company view could not load its latest quote, chart, or news.");
        toast.error("Market Pulse company view failed to load");
      } finally {
        if (active) setLoading(false);
      }
    };
    load();
    return () => {
      active = false;
    };
  }, [authLoaded, chartRange, rememberViewed, symbol, userId]);

  if (!marketsFeatureEnabled) {
    return <MarketDisabledState />;
  }

  const profile = detail ? (liveQuotes[detail.profile.displaySymbol] ?? detail.profile) : null;
  
  // Use normalized displaySymbol for watchlist check to avoid NS/BO suffix issues
  const currentDisplaySymbol = profile?.displaySymbol || symbol;
  const inWatchlist = watchlistSymbols.includes(currentDisplaySymbol);
  
  const latestAlert = alerts[0];

  const submitAlert = async () => {
    const value = Number(thresholdValue);
    if (!value) return;
    try {
      await marketsApi.addAlert({
        symbol: currentDisplaySymbol,
        exchange: detail?.profile.exchange ?? "NSE",
        alertType,
        thresholdValue: value,
      });
      toast.success("Alert created");
      const refreshed = await marketsApi.alerts();
      setAlerts(refreshed.data.filter((item: PriceAlert) => item.symbol === currentDisplaySymbol));
      setThresholdValue("");
    } catch {
      toast.error("Alert creation failed");
    }
  };

  const toggleWatchlistRemote = async () => {
    try {
      toggleWatchlistSymbol(currentDisplaySymbol);
      if (inWatchlist) {
        await marketsApi.deleteWatchlist(currentDisplaySymbol);
      } else {
        await marketsApi.addWatchlist({ 
          symbol: currentDisplaySymbol, 
          exchange: detail?.profile.exchange ?? "NSE" 
        });
      }
      toast.success(inWatchlist ? "Removed from watchlist" : "Added to watchlist");
    } catch {
      toggleWatchlistSymbol(currentDisplaySymbol);
      toast.error("Watchlist update failed");
    }
  };

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

  const shareholdingData = useMemo(
    () => detail?.shareholding.map((item) => ({ ...item, value: item.percent })) ?? [],
    [detail?.shareholding]
  );

  return (
    <div className="market-shell space-y-6 rounded-[28px] p-4 md:p-6">
      {/* ── Breadcrumbs / Top Navigation ── */}
      <nav className="flex items-center gap-2 text-xs font-medium uppercase tracking-[0.12em] text-slate-500">
        <Link href="/markets" className="flex items-center gap-1.5 transition hover:text-white">
          <Home className="h-3 w-3" />
          Markets
        </Link>
        <span className="text-slate-700">/</span>
        <span className="text-slate-300">{currentDisplaySymbol}</span>
      </nav>

      {loadError && !loading && (!detail || !chart) ? (
        <section className="market-card p-5 md:p-6">
          <p className="market-eyebrow">Connection Issue</p>
          <h2 className="mt-2 text-2xl font-semibold text-white">Company data is temporarily unavailable</h2>
          <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-300">{loadError}</p>
          <Link href="/markets" className="btn-primary mt-5 inline-flex items-center gap-2">
            <ArrowLeft className="h-4 w-4" />
            Back to Markets
          </Link>
        </section>
      ) : null}

      {loading || !detail || !profile || !chart ? (
        <div className="grid gap-4 xl:grid-cols-[1.4fr,0.9fr]">
          {Array.from({ length: 6 }).map((_, index) => (
            <div key={index} className="market-card h-44 animate-pulse bg-white/5" />
          ))}
        </div>
      ) : (
        <>
          <section className="market-card overflow-hidden">
            <div className="flex flex-col lg:flex-row">
              <div className="flex-1 p-5 md:p-8">
                <div className="flex items-center gap-3">
                  <Link 
                    href="/markets" 
                    className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/5 text-slate-400 transition hover:bg-white/10 hover:text-white"
                  >
                    <ArrowLeft className="h-5 w-5" />
                  </Link>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="market-pill text-[10px] font-bold">{profile.exchange}</span>
                    <span className={cn(
                      "market-pill text-[10px] font-bold uppercase",
                      profile.marketStatus === "live" ? "border-emerald-500/30 text-emerald-400" : "text-slate-500"
                    )}>
                      {profile.marketStatus}
                    </span>
                  </div>
                </div>

                <div className="mt-6 flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
                  <div>
                    <p className="text-sm font-medium tracking-wide text-emerald-400/80">{profile.sector}</p>
                    <h1 className="mt-1 text-4xl font-bold tracking-tight text-white md:text-5xl">
                      {profile.companyName}
                    </h1>
                    <div className="mt-4 flex items-baseline gap-4">
                      <p className="text-4xl font-semibold text-white">
                        {formatCurrency(profile.currentPrice)}
                      </p>
                      <div className={cn(
                        "flex items-center gap-1 rounded-lg px-2.5 py-1 text-sm font-bold",
                        profile.changePct >= 0 ? "bg-emerald-500/10 text-emerald-400" : "bg-rose-500/10 text-rose-400"
                      )}>
                        {profile.changePct >= 0 ? "+" : ""}{formatPercent(profile.changePct)}
                      </div>
                    </div>
                  </div>

                  <div className="flex flex-col gap-3 sm:flex-row">
                    <button 
                      onClick={toggleWatchlistRemote} 
                      className={cn(
                        "flex items-center justify-center gap-2 rounded-2xl px-6 py-3.5 text-sm font-bold transition-all active:scale-95",
                        inWatchlist 
                          ? "bg-emerald-500 text-white shadow-[0_0_20px_rgba(16,185,129,0.3)]" 
                          : "bg-white/10 text-white hover:bg-white/15"
                      )}
                    >
                      {inWatchlist ? <CheckCircle2 className="h-4.5 w-4.5" /> : <Star className="h-4.5 w-4.5" />}
                      {inWatchlist ? "In Watchlist" : "Add to Watchlist"}
                    </button>
                  </div>
                </div>

                <div className="mt-8 grid gap-4 border-t border-white/[0.06] pt-8 sm:grid-cols-3">
                  <HeaderStat label="52W High" value={detail.stats.week52High ? formatCurrency(detail.stats.week52High) : "NA"} />
                  <HeaderStat label="52W Low" value={detail.stats.week52Low ? formatCurrency(detail.stats.week52Low) : "NA"} />
                  <HeaderStat label="Market Cap" value={detail.stats.marketCap ? formatLargeNumber(detail.stats.marketCap) : "NA"} />
                </div>
              </div>

              <div className="border-t border-white/[0.08] bg-white/[0.02] p-5 md:p-8 lg:w-[360px] lg:border-l lg:border-t-0">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold uppercase tracking-widest text-slate-500">Price Alerts</h3>
                  <BellRing className="h-4 w-4 text-slate-500" />
                </div>
                <div className="mt-6 grid gap-3">
                  <div className="grid grid-cols-2 gap-2">
                    <select
                      value={alertType}
                      onChange={(event) => setAlertType(event.target.value as typeof alertType)}
                      className="market-input text-xs"
                    >
                      <option value="price_above">Above</option>
                      <option value="price_below">Below</option>
                      <option value="pct_change">% Move</option>
                    </select>
                    <input
                      value={thresholdValue}
                      onChange={(event) => setThresholdValue(event.target.value)}
                      placeholder="Value"
                      className="market-input text-xs"
                    />
                  </div>
                  <button onClick={submitAlert} className="btn-primary w-full justify-center py-3 font-bold">
                    Create Alert
                  </button>
                </div>
                {latestAlert && (
                  <div className="mt-4 rounded-xl bg-white/[0.04] p-3 text-[11px] text-slate-400">
                    <span className="font-medium text-slate-300">Active Alert:</span> {latestAlert.alertType.replace("_", " ")} at {latestAlert.thresholdValue}
                  </div>
                )}
              </div>
            </div>
          </section>

          <section className="space-y-4">
            <div className="market-card p-4 md:p-5">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex flex-wrap gap-2">
                  {ranges.map((range) => (
                    <button
                      key={range}
                      onClick={() => setChartRange(range)}
                      className={cn(
                        "rounded-full border px-3 py-1.5 text-xs transition",
                        chartRange === range
                          ? "border-emerald-400/30 bg-emerald-400/10 text-emerald-200"
                          : "border-white/10 bg-white/5 text-slate-300 hover:bg-white/10"
                      )}
                    >
                      {range}
                    </button>
                  ))}
                </div>
                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={() => setChartMode("candle")}
                    className={cn(
                      "rounded-full border px-3 py-1.5 text-xs transition",
                      chartMode === "candle"
                        ? "border-white/20 bg-white/[0.12] text-white"
                        : "border-white/10 bg-white/5 text-slate-300"
                    )}
                  >
                    <CandlestickChart className="mr-1 inline h-3.5 w-3.5" />
                    Candles
                  </button>
                  <button
                    onClick={() => setChartMode("line")}
                    className={cn(
                      "rounded-full border px-3 py-1.5 text-xs transition",
                      chartMode === "line"
                        ? "border-white/20 bg-white/[0.12] text-white"
                        : "border-white/10 bg-white/5 text-slate-300"
                    )}
                  >
                    <LineChartIcon className="mr-1 inline h-3.5 w-3.5" />
                    Line
                  </button>
                </div>
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                {indicators.map((indicator) => (
                  <button
                    key={indicator}
                    onClick={() => toggleIndicator(indicator)}
                    className={cn(
                      "rounded-full border px-3 py-1.5 text-xs transition",
                      selectedIndicators.includes(indicator)
                        ? "border-emerald-400/30 bg-emerald-400/10 text-emerald-200"
                        : "border-white/10 bg-white/5 text-slate-300"
                    )}
                  >
                    {indicator}
                  </button>
                ))}
              </div>
              <div className="mt-5">
                <MarketChart
                  points={chart.points}
                  range={chartRange}
                  mode={chartMode}
                  indicators={selectedIndicators}
                />
              </div>
            </div>
          </section>

          <Tabs.Root defaultValue="overview">
            <Tabs.List className="flex items-center gap-1 rounded-2xl bg-white/[0.03] p-1.5 backdrop-blur-md">
              {["overview", "financials", "news", "peers", "ownership"].map((tab) => (
                <Tabs.Trigger
                  key={tab}
                  value={tab}
                  className="flex-1 rounded-xl px-4 py-2.5 text-xs font-bold uppercase tracking-widest text-slate-400 transition-all data-[state=active]:bg-white/10 data-[state=active]:text-emerald-400 data-[state=active]:shadow-lg"
                >
                  {tab === "news" ? "News Impact" : tab}
                </Tabs.Trigger>
              ))}
            </Tabs.List>

            <Tabs.Content value="overview" className="mt-6 grid gap-6 xl:grid-cols-[1.25fr,0.95fr] animate-in fade-in slide-in-from-bottom-4 duration-500">
              <div className="space-y-6">
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  <StatCard label="P/E Ratio" value={detail.stats.peRatio?.toFixed(2) ?? "NA"} />
                  <StatCard label="EPS" value={detail.stats.eps ? formatCurrency(detail.stats.eps) : "NA"} />
                  <StatCard label="Dividend Yield" value={detail.stats.dividendYield ? `${detail.stats.dividendYield.toFixed(2)}%` : "NA"} />
                  <StatCard label="Beta" value={detail.stats.beta?.toFixed(2) ?? "NA"} />
                  <StatCard label="Book Value" value={detail.stats.bookValue ? formatCurrency(detail.stats.bookValue) : "NA"} />
                  <StatCard label="Avg Volume" value={detail.stats.avgVolume ? detail.stats.avgVolume.toLocaleString("en-IN") : "NA"} />
                </div>
                <div className="market-card p-6 md:p-8">
                  <h3 className="text-sm font-bold uppercase tracking-[0.2em] text-slate-500">Analyst Consensus</h3>
                  <div className="mt-8 grid gap-4 sm:grid-cols-4">
                    <StatCard label="Rating" value={detail.analystConsensus.rating} />
                    <StatCard label="Buy" value={detail.analystConsensus.buy.toString()} />
                    <StatCard label="Hold" value={detail.analystConsensus.hold.toString()} />
                    <StatCard label="Sell" value={detail.analystConsensus.sell.toString()} />
                  </div>
                  <p className="mt-6 text-sm text-slate-400">
                    Target price {detail.analystConsensus.targetPrice ? formatCurrency(detail.analystConsensus.targetPrice) : "not available"}.
                  </p>
                </div>
              </div>
              <div className="space-y-6">
                <div className="market-card p-6 md:p-8">
                  <h3 className="text-sm font-bold uppercase tracking-[0.2em] text-slate-500">Portfolio Context</h3>
                  {detail.portfolioPosition ? (
                    <div className="mt-6 space-y-4">
                      <StatCard label="Quantity" value={detail.portfolioPosition.quantity.toFixed(2)} />
                      <StatCard label="Current Value" value={formatCurrency(detail.portfolioPosition.currentValue)} />
                      <StatCard label="Unrealized P&L" value={formatCurrency(detail.portfolioPosition.unrealizedPnl)} />
                      <div className={cn(
                        "inline-flex rounded-full px-3 py-1 text-[11px] font-bold uppercase tracking-wider",
                        detail.portfolioPosition.unrealizedPnlPct >= 0 ? "bg-emerald-500/10 text-emerald-400" : "bg-rose-500/10 text-rose-400"
                      )}>
                        {formatPercent(detail.portfolioPosition.unrealizedPnlPct)} since entry
                      </div>
                    </div>
                  ) : (
                    <p className="mt-6 text-sm text-slate-400 italic">This symbol is not currently held in your connected portfolio.</p>
                  )}
                </div>
                <div className="market-card p-6 md:p-8">
                  <h3 className="text-sm font-bold uppercase tracking-[0.2em] text-slate-500">Peer Snapshot</h3>
                  <div className="mt-8 space-y-3">
                    {detail.peers.map((peer) => (
                      <Link key={peer.displaySymbol} href={`/markets/${peer.displaySymbol}`} className="market-inline-row group">
                        <div>
                          <p className="font-bold text-white transition group-hover:text-emerald-400">{peer.displaySymbol}</p>
                          <p className="text-[10px] text-slate-500 uppercase tracking-wider">{peer.companyName}</p>
                        </div>
                        <div className="text-right">
                          <p className="font-semibold text-white">{formatCurrency(peer.currentPrice)}</p>
                          <p className={cn("text-[11px] font-bold", peer.changePct >= 0 ? "text-emerald-400" : "text-rose-400")}>
                            {peer.changePct >= 0 ? "+" : ""}{formatPercent(peer.changePct)}
                          </p>
                        </div>
                      </Link>
                    ))}
                  </div>
                </div>
              </div>
            </Tabs.Content>

            <Tabs.Content value="financials" className="mt-6 grid gap-6 xl:grid-cols-2 animate-in fade-in slide-in-from-bottom-4 duration-500">
              <FinancialTable title="Quarterly Growth" rows={detail.financials.quarterly} />
              <FinancialTable title="Annual Performance" rows={detail.financials.annual} />
            </Tabs.Content>

            <Tabs.Content value="news" className="mt-6 space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
              {news.length ? news.map((article) => (
                <MarketNewsCard key={article.id} article={article} onToggleBookmark={toggleBookmarkRemote} />
              )) : (
                <div className="market-card flex flex-col items-center justify-center p-12 text-center">
                  <p className="text-slate-400">No company-specific news impact analyzed recently.</p>
                </div>
              )}
            </Tabs.Content>

            <Tabs.Content value="peers" className="mt-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
              <div className="market-card overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full table-auto border-collapse">
                    <thead className="bg-white/5 text-left text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">
                      <tr>
                        <th className="px-6 py-4">Symbol</th>
                        <th className="px-6 py-4">Current Price</th>
                        <th className="px-6 py-4">24h Change</th>
                        <th className="px-6 py-4">P/E Ratio</th>
                        <th className="px-6 py-4">Market Cap</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/[0.06]">
                      {detail.peers.map((peer) => (
                        <tr key={peer.displaySymbol} className="group transition hover:bg-white/[0.02]">
                          <td className="px-6 py-4">
                            <Link href={`/markets/${peer.displaySymbol}`} className="font-bold text-white transition group-hover:text-emerald-400">
                              {peer.displaySymbol}
                            </Link>
                          </td>
                          <td className="px-6 py-4 font-medium text-slate-300">{formatCurrency(peer.currentPrice)}</td>
                          <td className="px-6 py-4">
                            <span className={cn("font-bold", peer.changePct >= 0 ? "text-emerald-400" : "text-rose-400")}>
                              {peer.changePct >= 0 ? "+" : ""}{formatPercent(peer.changePct)}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-slate-400">{peer.peRatio?.toFixed(2) ?? "NA"}</td>
                          <td className="px-6 py-4 text-slate-400">{peer.marketCap ? formatLargeNumber(peer.marketCap) : "NA"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </Tabs.Content>

            <Tabs.Content value="ownership" className="mt-6 grid gap-6 xl:grid-cols-[0.8fr,1.2fr] animate-in fade-in slide-in-from-bottom-4 duration-500">
              <div className="market-card flex flex-col items-center justify-center p-8">
                <h3 className="mb-8 self-start text-sm font-bold uppercase tracking-[0.2em] text-slate-500">Shareholding Pattern</h3>
                <div className="h-[260px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie 
                        data={shareholdingData} 
                        dataKey="value" 
                        nameKey="label" 
                        innerRadius={70} 
                        outerRadius={100} 
                        paddingAngle={4}
                        stroke="none"
                      >
                        {shareholdingData.map((slice) => (
                          <Cell key={slice.label} fill={slice.color} className="outline-none" />
                        ))}
                      </Pie>
                      <RechartsTooltip 
                        contentStyle={{ backgroundColor: "#0f172a", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "12px" }}
                        itemStyle={{ color: "#fff", fontSize: "12px" }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                {detail.shareholding.map((slice) => (
                  <div key={slice.label} className="market-card flex items-center justify-between p-5">
                    <div className="flex items-center gap-3">
                      <div className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: slice.color }} />
                      <p className="text-sm font-bold text-white">{slice.label}</p>
                    </div>
                    <p className="text-xl font-bold text-white">{slice.percent.toFixed(2)}%</p>
                  </div>
                ))}
              </div>
            </Tabs.Content>
          </Tabs.Root>
        </>
      )}
    </div>
  );
}

function HeaderStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-white/[0.08] bg-black/20 px-4 py-3">
      <p className="text-[11px] uppercase tracking-[0.24em] text-slate-500">{label}</p>
      <p className="mt-2 text-lg font-semibold text-white">{value}</p>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-white/[0.08] bg-black/20 p-4">
      <p className="text-[11px] uppercase tracking-[0.24em] text-slate-500">{label}</p>
      <p className="mt-2 text-xl font-semibold text-white">{value}</p>
    </div>
  );
}

function FinancialTable({
  title,
  rows,
}: {
  title: string;
  rows: CompanyDetailResponse["financials"]["quarterly"];
}) {
  return (
    <div className="overflow-hidden rounded-3xl border border-white/[0.08]">
      <div className="border-b border-white/[0.08] bg-white/5 px-4 py-3 text-sm font-medium text-white">{title}</div>
      <table className="w-full table-auto">
        <thead className="text-left text-xs uppercase tracking-[0.24em] text-slate-500">
          <tr>
            <th className="px-4 py-3">Period</th>
            <th className="px-4 py-3">Revenue</th>
            <th className="px-4 py-3">Net Profit</th>
            <th className="px-4 py-3">OCF</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={`${title}-${row.period}`} className="border-t border-white/[0.08] text-sm text-slate-200">
              <td className="px-4 py-3">{row.period}</td>
              <td className="px-4 py-3">{row.revenue ? formatLargeNumber(row.revenue) : "NA"}</td>
              <td className="px-4 py-3">{row.netProfit ? formatLargeNumber(row.netProfit) : "NA"}</td>
              <td className="px-4 py-3">{row.operatingCashFlow ? formatLargeNumber(row.operatingCashFlow) : "NA"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
