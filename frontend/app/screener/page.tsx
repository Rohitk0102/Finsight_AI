"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { screenerApi } from "@/lib/api/client";
import { useMarketPulseStore } from "@/lib/markets/store";
import { formatCurrency, formatChange } from "@/lib/utils";
import { Search, Loader2, Star, Bookmark, SlidersHorizontal, Zap, BarChart3, TrendingUp, DollarSign, Cpu, X } from "lucide-react";
import { toast } from "sonner";

interface StockResult {
  ticker: string; name: string; current_price: number;
  price_change_pct: number; market_cap: number | null;
  pe_ratio: number | null; sector: string | null;
}

export default function ScreenerPage() {
  const [filters, setFilters] = useState({ exchange: "NSE", sector: "", min_market_cap: "", max_pe: "" });
  const [results,   setResults]   = useState<StockResult[]>([]);
  const [loading,   setLoading]   = useState(false);
  const [metadata,  setMetadata]  = useState<{ sectors: string[], exchanges: string[] }>({ sectors: [], exchanges: [] });
  
  const watchlistSymbols = useMarketPulseStore((state) => state.watchlistSymbols);
  const toggleWatchlistSymbol = useMarketPulseStore((state) => state.toggleWatchlistSymbol);
  const setWatchlistSymbols = useMarketPulseStore((state) => state.setWatchlistSymbols);

  const presets = [
    { 
      id: "growth", 
      label: "Growth Tech", 
      icon: Zap, 
      color: "text-blue-500",
      desc: "Tech giants with strong momentum",
      params: { exchange: "NASDAQ", sector: "Technology", min_market_cap: "100000000000", max_pe: "100" } 
    },
    { 
      id: "value", 
      label: "Value Plays", 
      icon: DollarSign, 
      color: "text-emerald-500",
      desc: "Low P/E ratios in current sector",
      params: { min_market_cap: "50000000000", max_pe: "15" } 
    },
    { 
      id: "giants", 
      label: "Market Leaders", 
      icon: TrendingUp, 
      color: "text-purple-500",
      desc: "Largest companies in current sector",
      params: { min_market_cap: "1000000000000", max_pe: "50" } 
    },
    { 
      id: "active", 
      label: "Small Cap Action", 
      icon: BarChart3, 
      color: "text-orange-500",
      desc: "High potential smaller companies",
      params: { min_market_cap: "5000000000", max_pe: "30" } 
    },
  ];

  useEffect(() => {
    const fetchMetadata = async () => {
      try {
        const res = await screenerApi.metadata();
        const data = res?.data || {};
        setMetadata({
          sectors: data.sectors || [],
          exchanges: data.exchanges || [],
        });
      } catch (error) {
        console.error("Failed to fetch screener metadata", error);
      }
    };
    const fetchWatchlist = async () => {
      try {
        const res = await screenerApi.watchlist();
        const tickers = (res?.data || []).map((item: any) => item.ticker);
        setWatchlistSymbols(tickers);
      } catch (error) {
        console.error("Failed to fetch watchlist", error);
      }
    };
    fetchMetadata();
    fetchWatchlist();
  }, [setWatchlistSymbols]);

  const applyPreset = (presetParams: Partial<typeof filters>) => {
    const newFilters = { ...filters, ...presetParams };
    setFilters(newFilters);
    handleScan(newFilters);
    toast.success(`Applied strategy to ${newFilters.sector || "all sectors"}`);
  };

  const handleScan = async (overrideFilters?: typeof filters) => {
    const activeFilters = overrideFilters || filters;
    setLoading(true);
    // results are NOT cleared here to avoid jumpy UI, but we could clear them if preferred
    try {
      const params: Record<string, unknown> = { exchange: activeFilters.exchange };
      if (activeFilters.sector)          params.sector          = activeFilters.sector;
      if (activeFilters.min_market_cap)  params.min_market_cap  = Number(activeFilters.min_market_cap);
      if (activeFilters.max_pe)          params.max_pe          = Number(activeFilters.max_pe);
      const res = await screenerApi.scan(params);
      const data = res?.data || [];
      setResults(data);
      if (data.length === 0) toast.info("No stocks matched your filters");
    } catch {
      toast.error("Screener scan failed");
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key: keyof typeof filters, value: string) => {
    const next = { ...filters, [key]: value };
    setFilters(next);
    // Auto-scan for dropdowns
    if (key === "exchange" || key === "sector") {
      handleScan(next);
    }
  };

  const resetFilters = () => {
    const defaults = { exchange: "NSE", sector: "", min_market_cap: "", max_pe: "" };
    setFilters(defaults);
    setResults([]);
    toast.success("Filters reset");
  };

  const toggleWatchlist = async (ticker: string) => {
    const inList = watchlistSymbols.includes(ticker);
    try {
      if (inList) {
        await screenerApi.removeFromWatchlist(ticker);
        toggleWatchlistSymbol(ticker);
        toast.success(`${ticker} removed from watchlist`);
      } else {
        await screenerApi.addToWatchlist(ticker);
        toggleWatchlistSymbol(ticker);
        toast.success(`${ticker} added to watchlist`);
      }
    } catch (error: any) {
      console.error("Watchlist update error:", error);
      const msg = error.response?.data?.detail || "Watchlist update failed";
      toast.error(msg);
    }
  };

  return (
    <div className="max-w-7xl">
      {/* Header */}
      <div className="mb-6 flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-page-title">Stock Screener</h1>
          <p className="text-body-sm text-muted-foreground mt-0.5">
            Filter stocks by fundamentals and technicals
          </p>
        </div>
        <div className="flex items-center gap-2">
           <div className="badge badge-primary bg-primary/10 text-primary border-primary/20">
             {results.length > 0 ? `${results.length} Stocks Found` : "Ready to scan"}
           </div>
        </div>
      </div>

      {/* Quick Presets */}
      <div className="mb-8 animate-fade-in">
        <h3 className="text-label-xs font-bold text-muted-foreground uppercase tracking-widest mb-3 ml-1">Quick Presets</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {presets.map((p) => (
            <button
              key={p.id}
              onClick={() => applyPreset(p.params)}
              className="card-surface p-4 text-left hover:border-primary/50 transition-all hover:shadow-md group flex items-start gap-4"
            >
              <div className={`w-10 h-10 rounded-xl bg-muted/50 flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform ${p.color}`}>
                <p.icon className="h-5 w-5" />
              </div>
              <div className="min-w-0">
                <p className="font-bold text-[14px] leading-tight group-hover:text-primary transition-colors">{p.label}</p>
                <p className="text-[11px] text-muted-foreground mt-1 line-clamp-2">{p.desc}</p>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Filter card */}
      <div className="card-surface p-5 mb-5 animate-slide-in-up">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <SlidersHorizontal className="h-4 w-4" style={{ color: "hsl(var(--primary))" }} />
            <span className="text-card-title font-semibold">Filters</span>
          </div>
          <button 
            onClick={resetFilters}
            className="text-[11px] font-bold text-muted-foreground hover:text-primary transition-colors flex items-center gap-1.5"
          >
            <X className="h-3 w-3" /> RESET FILTERS
          </button>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-5">
          {/* Exchange Select */}
          <div>
            <label className="text-label-xs text-muted-foreground mb-1.5 block font-medium">Exchange</label>
            <select
              value={filters.exchange}
              onChange={(e) => handleFilterChange("exchange", e.target.value)}
              className="input-field appearance-none cursor-pointer"
            >
              <option value="NSE">NSE</option>
              <option value="NASDAQ">NASDAQ</option>
              <option value="BSE">BSE</option>
              {metadata.exchanges.filter(e => !["NSE", "NASDAQ", "BSE"].includes(e)).map(e => (
                <option key={e} value={e}>{e}</option>
              ))}
            </select>
          </div>

          {/* Sector Select */}
          <div>
            <label className="text-label-xs text-muted-foreground mb-1.5 block font-medium">Sector</label>
            <select
              value={filters.sector}
              onChange={(e) => handleFilterChange("sector", e.target.value)}
              className="input-field appearance-none cursor-pointer"
            >
              <option value="">All Sectors</option>
              {metadata.sectors.map(s => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>

          {/* Market Cap Input */}
          <div>
            <label className="text-label-xs text-muted-foreground mb-1.5 block font-medium">Min Market Cap (₹)</label>
            <input
              type="number"
              value={filters.min_market_cap}
              onChange={(e) => handleFilterChange("min_market_cap", e.target.value)}
              placeholder="e.g. 10000000000"
              className="input-field"
            />
          </div>

          {/* P/E Input */}
          <div>
            <label className="text-label-xs text-muted-foreground mb-1.5 block font-medium">Max P/E Ratio</label>
            <input
              type="number"
              value={filters.max_pe}
              onChange={(e) => handleFilterChange("max_pe", e.target.value)}
              placeholder="e.g. 25"
              className="input-field"
            />
          </div>
        </div>

        <button
          onClick={() => handleScan()}
          disabled={loading}
          className="btn-primary px-6 py-2.5"
        >
          {loading
            ? <><Loader2 className="h-4 w-4 animate-spin" /> Scanning…</>
            : <><Search className="h-4 w-4" /> Scan Stocks</>
          }
        </button>
      </div>

      {/* Results */}
      {results.length > 0 && (
        <div className="animate-slide-in-up delay-75">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-card-title font-semibold">
              Results
              <span className="ml-2 badge badge-primary">{results.length}</span>
            </h2>
            {watchlistSymbols.length > 0 && (
              <span className="flex items-center gap-1 text-label-xs text-muted-foreground">
                <Bookmark className="h-3 w-3" /> {watchlistSymbols.length} watchlisted
              </span>
            )}
          </div>

          <div className="card-surface overflow-x-auto">
            <table className="w-full text-body-sm min-w-[600px] table-rows">
              <thead>
                <tr style={{ borderBottom: "1px solid hsl(var(--border))" }}>
                  <th className="px-5 py-3 text-left text-label-xs text-muted-foreground font-medium">Stock</th>
                  <th className="px-5 py-3 text-right text-label-xs text-muted-foreground font-medium">Price</th>
                  <th className="px-5 py-3 text-right text-label-xs text-muted-foreground font-medium">Change</th>
                  <th className="px-5 py-3 text-right text-label-xs text-muted-foreground font-medium hidden md:table-cell">Mkt Cap</th>
                  <th className="px-5 py-3 text-right text-label-xs text-muted-foreground font-medium hidden md:table-cell">P/E</th>
                  <th className="px-5 py-3 text-center text-label-xs text-muted-foreground font-medium">AI Match</th>
                  <th className="px-5 py-3 text-center text-label-xs text-muted-foreground font-medium">Watch</th>
                </tr>
              </thead>
              <tbody>
                {results.map((s, i) => {
                  const chg = formatChange(s.price_change_pct);
                  const inWL = watchlistSymbols.includes(s.ticker);
                  const isAIMatch = s.pe_ratio && s.pe_ratio < 25 && s.price_change_pct > 0;

                  return (
                    <tr
                      key={s.ticker}
                      className="animate-slide-in-up"
                      style={{ animationDelay: `${Math.min(i * 30, 600)}ms` }}
                    >
                      <td className="px-5 py-3.5">
                        <Link 
                          href={`/markets/${s.ticker}`}
                          className="font-semibold text-[13px] text-primary hover:underline block"
                        >
                          {s.ticker}
                        </Link>
                        <p className="text-[11px] text-muted-foreground truncate max-w-[120px]">{s.name}</p>
                      </td>
                      <td className="px-5 py-3.5 text-right font-semibold text-[13px]">
                        {formatCurrency(s.current_price)}
                      </td>
                      <td className={`px-5 py-3.5 text-right font-semibold text-[13px] ${chg.colorClass}`}>
                        {chg.symbol} {chg.text}
                      </td>
                      <td className="px-5 py-3.5 text-right text-muted-foreground text-[13px] hidden md:table-cell">
                        {s.market_cap ? `₹${(s.market_cap / 1e7).toFixed(0)}Cr` : "—"}
                      </td>
                      <td className="px-5 py-3.5 text-right text-muted-foreground text-[13px] hidden md:table-cell">
                        {s.pe_ratio?.toFixed(1) || "—"}
                      </td>
                      <td className="px-5 py-3.5 text-center">
                        {isAIMatch ? (
                          <div className="inline-flex items-center gap-1 px-2 py-0.5 bg-primary/10 text-primary text-[10px] font-bold rounded-full border border-primary/20">
                            <Cpu className="h-2.5 w-2.5" /> High Signal
                          </div>
                        ) : (
                          <span className="text-[10px] text-muted-foreground">Analysing...</span>
                        )}
                      </td>
                      <td className="px-5 py-3.5 text-center">
                        <button
                          onClick={() => toggleWatchlist(s.ticker)}
                          className="transition-all hover:scale-125 inline-flex"
                          title={inWL ? "Remove from watchlist" : "Add to watchlist"}
                        >
                          <Star
                            className="h-4 w-4"
                            style={{
                              color: inWL ? "hsl(var(--primary))" : "hsl(var(--muted-foreground))",
                              fill:  inWL ? "hsl(var(--primary))" : "none",
                            }}
                          />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Empty state */}
      {results.length === 0 && !loading && (
        <div className="text-center py-20 animate-fade-in">
          <div
            className="kpi-icon-circle mx-auto mb-4"
            style={{ background: "hsl(var(--primary) / 0.08)", width: "64px", height: "64px" }}
          >
            <Search className="h-7 w-7 opacity-40" style={{ color: "hsl(var(--primary))" }} />
          </div>
          <p className="text-card-title font-medium text-muted-foreground mb-1">No results yet</p>
          <p className="text-body-sm text-muted-foreground">Set your filters and run a scan</p>
        </div>
      )}
    </div>
  );
}
