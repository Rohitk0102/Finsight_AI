import { beforeEach, describe, expect, it } from "vitest";
import { useMarketPulseStore } from "@/lib/markets/store";

describe("market pulse store", () => {
  beforeEach(() => {
    const storage = new Map<string, string>();
    Object.defineProperty(window, "localStorage", {
      value: {
        getItem: (key: string) => storage.get(key) ?? null,
        setItem: (key: string, value: string) => storage.set(key, value),
        removeItem: (key: string) => storage.delete(key),
      },
      configurable: true,
    });

    useMarketPulseStore.setState({
      activeSymbol: null,
      chartRange: "1Y",
      chartMode: "candle",
      indicators: ["SMA", "EMA", "Bollinger"],
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
    });
  });

  it("remembers recent searches without duplicates", () => {
    const result = {
      symbol: "RELIANCE.NS",
      displaySymbol: "RELIANCE",
      exchange: "NSE",
      companyName: "Reliance Industries",
      sector: "Energy",
      currentPrice: 2840,
      change: 10,
      changePct: 0.35,
      marketStatus: "live" as const,
      lastUpdated: new Date().toISOString(),
    };
    useMarketPulseStore.getState().rememberSearch(result);
    useMarketPulseStore.getState().rememberSearch(result);

    expect(useMarketPulseStore.getState().recentSearches).toHaveLength(1);
    expect(useMarketPulseStore.getState().recentSearches[0].displaySymbol).toBe("RELIANCE");
  });

  it("toggles watchlist symbols", () => {
    useMarketPulseStore.getState().toggleWatchlistSymbol("INFY");
    expect(useMarketPulseStore.getState().watchlistSymbols).toContain("INFY");
    useMarketPulseStore.getState().toggleWatchlistSymbol("INFY");
    expect(useMarketPulseStore.getState().watchlistSymbols).not.toContain("INFY");
  });
});
