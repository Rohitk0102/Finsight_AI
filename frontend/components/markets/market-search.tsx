"use client";

import { startTransition, useDeferredValue, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Mic, Search, TrendingUp, X } from "lucide-react";
import { toast } from "sonner";
import { marketsApi } from "@/lib/api/client";
import { useMarketPulseStore } from "@/lib/markets/store";
import type { SearchContextResponse, SearchResult } from "@/lib/markets/types";
import { cn, formatCurrency, formatPercent } from "@/lib/utils";

declare global {
  interface Window {
    webkitSpeechRecognition?: new () => any;
    SpeechRecognition?: new () => any;
  }
}

interface MarketSearchProps {
  context: SearchContextResponse | null;
}

export function MarketSearch({ context }: MarketSearchProps) {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [voiceSupported, setVoiceSupported] = useState(false);
  const recognitionRef = useRef<any>(null);
  const requestIdRef = useRef(0);
  const recentSearches = useMarketPulseStore((state) => state.recentSearches);
  const rememberSearch = useMarketPulseStore((state) => state.rememberSearch);
  const setSearchFocused = useMarketPulseStore((state) => state.setSearchFocused);
  const deferredQuery = useDeferredValue(query);

  useEffect(() => {
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    setVoiceSupported(Boolean(Recognition));
  }, []);

  useEffect(() => {
    if (!deferredQuery.trim()) {
      setResults([]);
      return;
    }

    const requestId = ++requestIdRef.current;
    const handle = window.setTimeout(async () => {
      try {
        setLoading(true);
        const response = await marketsApi.search(deferredQuery.trim());
        if (requestId !== requestIdRef.current) return;
        startTransition(() => {
          setResults(response.data);
        });
      } catch {
        if (requestId === requestIdRef.current) {
          toast.error("Market search is temporarily unavailable");
        }
      } finally {
        if (requestId === requestIdRef.current) {
          setLoading(false);
        }
      }
    }, 220);

    return () => window.clearTimeout(handle);
  }, [deferredQuery]);

  const quickItems = useMemo(() => {
    if (query.trim()) return results;
    return context?.trending ?? [];
  }, [context?.trending, query, results]);

  const openSymbol = (result: SearchResult) => {
    rememberSearch(result);
    router.push(`/markets/${result.displaySymbol}`);
    setOpen(false);
    setQuery("");
  };

  const startVoiceSearch = () => {
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) return;
    const recognition = new Recognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "en-IN";
    recognition.onresult = (event: any) => {
      const transcript = event.results[0]?.[0]?.transcript ?? "";
      setQuery(transcript);
      setOpen(true);
    };
    recognition.onerror = () => {
      toast.error("Voice search could not start");
    };
    recognitionRef.current = recognition;
    recognition.start();
  };

  const historyItems = recentSearches.slice(0, 6);

  return (
    <div className="relative">
      <div className="market-search-shell">
        <Search className="h-5 w-5 text-slate-400" />
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          onFocus={() => {
            setOpen(true);
            setSearchFocused(true);
          }}
          onBlur={() => {
            window.setTimeout(() => {
              setOpen(false);
              setSearchFocused(false);
            }, 120);
          }}
          onKeyDown={(event) => {
            if (event.key === "Escape") {
              setQuery("");
              setOpen(false);
            }
          }}
          placeholder="Search Tata, RELIANCE, budget 2025"
          className="min-w-0 flex-1 bg-transparent text-[15px] text-white outline-none placeholder:text-slate-500"
        />
        {query && (
          <button
            onClick={() => setQuery("")}
            className="rounded-full p-1 text-slate-400 transition hover:bg-white/10 hover:text-white"
            aria-label="Clear search"
          >
            <X className="h-4 w-4" />
          </button>
        )}
        {voiceSupported && (
          <button
            onClick={startVoiceSearch}
            className="rounded-full border border-white/10 bg-white/5 p-2 text-slate-300 transition hover:bg-white/10 hover:text-white"
            aria-label="Start voice search"
          >
            <Mic className="h-4 w-4" />
          </button>
        )}
      </div>

      {open && (
        <div className="market-search-panel">
          {!query.trim() && (
            <div className="grid gap-5 md:grid-cols-2">
              <div>
                <p className="market-eyebrow">Search History</p>
                <div className="mt-3 space-y-2">
                  {historyItems.length ? historyItems.map((item) => (
                    <button
                      key={`history-${item.displaySymbol}`}
                      onMouseDown={() => openSymbol(item)}
                      className="market-search-item"
                    >
                      <div className="market-avatar">{item.displaySymbol.slice(0, 1)}</div>
                      <div className="min-w-0 flex-1 text-left">
                        <p className="truncate text-sm font-medium text-white">{item.companyName}</p>
                        <p className="text-xs text-slate-400">{item.displaySymbol} · {item.exchange}</p>
                      </div>
                    </button>
                  )) : (
                    <p className="text-sm text-slate-400">Recent searches will appear here after your first lookup.</p>
                  )}
                </div>
              </div>
              <div>
                <p className="market-eyebrow">Trending Tickers</p>
                <div className="mt-3 space-y-2">
                  {(context?.trending ?? []).map((item) => (
                    <button
                      key={`trend-${item.displaySymbol}`}
                      onMouseDown={() => openSymbol(item)}
                      className="market-search-item"
                    >
                      <div className="market-avatar bg-emerald-500/[0.12] text-emerald-200">
                        <TrendingUp className="h-4 w-4" />
                      </div>
                      <div className="min-w-0 flex-1 text-left">
                        <p className="truncate text-sm font-medium text-white">{item.companyName}</p>
                        <p className="text-xs text-slate-400">{item.displaySymbol} · {item.exchange}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-semibold text-white">{formatCurrency(item.currentPrice)}</p>
                        <p className={cn("text-xs", item.changePct >= 0 ? "text-emerald-300" : "text-rose-300")}>
                          {formatPercent(item.changePct)}
                        </p>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {query.trim() && (
            <div className="space-y-2">
              {loading && (
                <div className="space-y-2">
                  {Array.from({ length: 4 }).map((_, index) => (
                    <div key={index} className="h-16 animate-pulse rounded-2xl bg-white/5" />
                  ))}
                </div>
              )}

              {!loading && quickItems.map((item) => (
                <button
                  key={item.displaySymbol}
                  onMouseDown={() => openSymbol(item as SearchResult)}
                  className="market-search-item"
                >
                  <div className="market-avatar">{item.displaySymbol.slice(0, 1)}</div>
                  <div className="min-w-0 flex-1 text-left">
                    <p className="truncate text-sm font-medium text-white">{item.companyName}</p>
                    <p className="text-xs text-slate-400">{item.displaySymbol} · {item.exchange} · {item.sector ?? "Market"}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold text-white">{formatCurrency(item.currentPrice)}</p>
                    <p className={cn("text-xs", item.changePct >= 0 ? "text-emerald-300" : "text-rose-300")}>
                      {formatPercent(item.changePct)}
                    </p>
                  </div>
                </button>
              ))}

              {!loading && !quickItems.length && (
                <p className="py-6 text-center text-sm text-slate-400">
                  No exact matches yet. Try a company name, NSE/BSE symbol, or market keyword.
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
