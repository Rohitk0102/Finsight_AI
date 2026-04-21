"use client";

import { create } from "zustand";
import { persist, createJSONStorage, type StateStorage } from "zustand/middleware";
import type {
  ChartMode,
  ChartRange,
  EnrichedNewsArticle,
  IndicatorKey,
  MarketStatus,
  PriceSnapshot,
  SearchResult,
} from "@/lib/markets/types";

type SocketStatus = "idle" | "connecting" | "connected" | "reconnecting" | "disconnected" | "error";

interface NewsFilters {
  category: string;
  exchange: string;
  sector: string;
  marketCap: string;
  sentiment: string;
}

interface MarketPulseState {
  activeSymbol: string | null;
  chartRange: ChartRange;
  chartMode: ChartMode;
  indicators: IndicatorKey[];
  searchFocused: boolean;
  recentSearches: SearchResult[];
  recentlyViewed: string[];
  watchlistSymbols: string[];
  bookmarkedUrls: string[];
  breakingNewsCount: number;
  marketStatus: MarketStatus;
  newsFilters: NewsFilters;
  socketStatus: SocketStatus;
  subscribedSymbols: string[];
  liveQuotes: Record<string, PriceSnapshot>;
  setActiveSymbol: (symbol: string | null) => void;
  setChartRange: (range: ChartRange) => void;
  setChartMode: (mode: ChartMode) => void;
  toggleIndicator: (indicator: IndicatorKey) => void;
  setSearchFocused: (focused: boolean) => void;
  rememberSearch: (result: SearchResult) => void;
  rememberViewed: (symbol: string) => void;
  setWatchlistSymbols: (symbols: string[]) => void;
  toggleWatchlistSymbol: (symbol: string) => void;
  setBookmarkedUrls: (urls: string[]) => void;
  toggleBookmark: (url: string) => void;
  setBreakingNewsCount: (count: number) => void;
  setMarketStatus: (status: MarketStatus) => void;
  updateNewsFilters: (partial: Partial<NewsFilters>) => void;
  setSocketStatus: (status: SocketStatus) => void;
  setSubscribedSymbols: (symbols: string[]) => void;
  upsertLiveQuotes: (quotes: PriceSnapshot[]) => void;
}

const defaultIndicators: IndicatorKey[] = ["SMA", "EMA", "Bollinger"];

const noopStorage: StateStorage = {
  getItem: () => null,
  setItem: () => {},
  removeItem: () => {},
};

const browserStorage: StateStorage = {
  getItem: (name) => {
    if (typeof window === "undefined") return null;
    return window.localStorage.getItem(name);
  },
  setItem: (name, value) => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(name, value);
  },
  removeItem: (name) => {
    if (typeof window === "undefined") return;
    window.localStorage.removeItem(name);
  },
};

export const useMarketPulseStore = create<MarketPulseState>()(
  persist(
    (set, get) => ({
      activeSymbol: null,
      chartRange: "1Y",
      chartMode: "candle",
      indicators: defaultIndicators,
      searchFocused: false,
      recentSearches: [],
      recentlyViewed: [],
      watchlistSymbols: [],
      bookmarkedUrls: [],
      breakingNewsCount: 0,
      marketStatus: "closed",
      newsFilters: {
        category: "all",
        exchange: "all",
        sector: "all",
        marketCap: "all",
        sentiment: "all",
      },
      socketStatus: "idle",
      subscribedSymbols: [],
      liveQuotes: {},
      setActiveSymbol: (symbol) => set({ activeSymbol: symbol }),
      setChartRange: (range) => set({ chartRange: range }),
      setChartMode: (mode) => set({ chartMode: mode }),
      toggleIndicator: (indicator) =>
        set((state) => ({
          indicators: state.indicators.includes(indicator)
            ? state.indicators.filter((item) => item !== indicator)
            : [...state.indicators, indicator],
        })),
      setSearchFocused: (focused) => set({ searchFocused: focused }),
      rememberSearch: (result) =>
        set((state) => ({
          recentSearches: [result, ...state.recentSearches.filter((item) => item.displaySymbol !== result.displaySymbol)].slice(0, 8),
        })),
      rememberViewed: (symbol) =>
        set((state) => ({
          recentlyViewed: [symbol, ...state.recentlyViewed.filter((item) => item !== symbol)].slice(0, 10),
        })),
      setWatchlistSymbols: (symbols) => set({ watchlistSymbols: symbols }),
      toggleWatchlistSymbol: (symbol) =>
        set((state) => ({
          watchlistSymbols: state.watchlistSymbols.includes(symbol)
            ? state.watchlistSymbols.filter((item) => item !== symbol)
            : [symbol, ...state.watchlistSymbols],
        })),
      setBookmarkedUrls: (urls) => set({ bookmarkedUrls: urls }),
      toggleBookmark: (url) =>
        set((state) => ({
          bookmarkedUrls: state.bookmarkedUrls.includes(url)
            ? state.bookmarkedUrls.filter((item) => item !== url)
            : [url, ...state.bookmarkedUrls],
        })),
      setBreakingNewsCount: (count) => set({ breakingNewsCount: count }),
      setMarketStatus: (status) => set({ marketStatus: status }),
      updateNewsFilters: (partial) =>
        set((state) => ({
          newsFilters: {
            ...state.newsFilters,
            ...partial,
          },
        })),
      setSocketStatus: (status) => set({ socketStatus: status }),
      setSubscribedSymbols: (symbols) => set({ subscribedSymbols: symbols }),
      upsertLiveQuotes: (quotes) =>
        set((state) => {
          const next = { ...state.liveQuotes };
          for (const quote of quotes) {
            next[quote.displaySymbol] = quote;
          }
          return { liveQuotes: next };
        }),
    }),
    {
      name: "market-pulse-store",
      storage: createJSONStorage(() =>
        typeof window !== "undefined" ? browserStorage : noopStorage
      ),
      partialize: (state) => ({
        chartRange: state.chartRange,
        chartMode: state.chartMode,
        indicators: state.indicators,
        recentSearches: state.recentSearches,
        recentlyViewed: state.recentlyViewed,
        watchlistSymbols: state.watchlistSymbols,
        bookmarkedUrls: state.bookmarkedUrls,
        newsFilters: state.newsFilters,
      }),
    }
  )
);

export function mergeLiveQuote<T extends { profile?: PriceSnapshot; displaySymbol?: string }>(
  entity: T,
  liveQuotes: Record<string, PriceSnapshot>
) {
  if ("profile" in entity && entity.profile?.displaySymbol) {
    const live = liveQuotes[entity.profile.displaySymbol];
    if (!live) return entity;
    return {
      ...entity,
      profile: {
        ...entity.profile,
        ...live,
      },
    };
  }
  return entity;
}

export function mergeArticleBookmarks(
  articles: EnrichedNewsArticle[],
  bookmarkedUrls: string[]
) {
  return articles.map((article) => ({
    ...article,
    bookmarked: article.bookmarked || bookmarkedUrls.includes(article.sourceUrl),
  }));
}
