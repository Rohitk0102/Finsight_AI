import axios from "axios";
import https from "https";

function resolveApiUrl() {
  const configured = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

  // In the browser, prefer the Next.js same-origin rewrite proxy to avoid
  // local cross-origin HTTPS/CORS issues against the backend.
  if (typeof window !== "undefined") {
    return "/api/backend";
  }

  // Local fallback: if frontend is served over HTTP, prefer HTTP backend to avoid TLS mismatch.
  return configured;
}

const API_URL = resolveApiUrl();

// Create HTTPS agent that accepts self-signed certificates for development
const httpsAgent = typeof window === "undefined" && process.env.NODE_ENV !== "production"
  ? new https.Agent({
      rejectUnauthorized: false,
    })
  : undefined;

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
  httpsAgent,
});

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

type ClerkLike = {
  loaded?: boolean;
  session?: { getToken: () => Promise<string | null> };
};

async function getClerkTokenWithRetry(attempts = 6, waitMs = 120): Promise<string | null> {
  if (typeof window === "undefined") return null;

  const w = window as typeof window & { Clerk?: ClerkLike };
  for (let i = 0; i < attempts; i++) {
    try {
      const clerk = w.Clerk;
      if (clerk?.loaded && clerk.session) {
        const token = await clerk.session.getToken();
        if (token) return token;
      }
    } catch {
      // Ignore and retry a few times; Clerk can still be initializing.
    }
    await sleep(waitMs);
  }
  return null;
}

// Attach Clerk JWT to every request
apiClient.interceptors.request.use(async (config) => {
  try {
    const token = await getClerkTokenWithRetry();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  } catch {
    // Not authenticated — proceed without token
  }
  return config;
});

// Redirect to sign-in on 401 (guard against infinite loop on auth pages)
apiClient.interceptors.response.use(
  (res) => res,
  async (error) => {
    const status = error.response?.status;
    const original = error.config as (typeof error.config & { _authRetried?: boolean }) | undefined;

    // If Clerk token wasn't ready yet, retry once with a fresh token.
    if ((status === 401 || status === 403) && original && !original._authRetried) {
      const token = await getClerkTokenWithRetry(4, 150);
      if (token) {
        original._authRetried = true;
        original.headers = original.headers ?? {};
        original.headers.Authorization = `Bearer ${token}`;
        return apiClient(original);
      }
    }

    if ((status === 401 || status === 403) && typeof window !== "undefined") {
      const path = window.location.pathname;
      if (!path.startsWith("/sign-in") && !path.startsWith("/sign-up")) {
        window.location.href = "/sign-in";
      }
    }
    return Promise.reject(error);
  }
);

// ── Typed API functions ───────────────────────────────────────────────────────

export const stocksApi = {
  search: (q: string) => apiClient.get(`/stocks/search?q=${q}`),
  detail: (ticker: string) => apiClient.get(`/stocks/${ticker}`),
  ohlcv: (ticker: string, period = "1y") => apiClient.get(`/stocks/${ticker}/ohlcv?period=${period}`),
  livePrice: (ticker: string) => apiClient.get(`/stocks/${ticker}/price`),
};

export const predictApi = {
  predict: (ticker: string, riskProfile = "moderate", horizon = "medium") =>
    apiClient.get(`/predict/${ticker}?risk_profile=${riskProfile}&horizon=${horizon}`),
  portfolioAnalysis: () => apiClient.get("/predict/portfolio/analysis"),
  history: (ticker: string) => apiClient.get(`/predict/history/${ticker}`),
  getAccuracySummary: () => apiClient.get("/predict/accuracy/model/summary"),
};

export const newsApi = {
  list: (params: {
    page?: number;
    limit?: number;
    ticker?: string;
    category?: string;
    sentiment?: string;
    time_range?: "1h" | "6h" | "24h" | "7d" | "30d";
  }) => apiClient.get("/news", { params }),
  market: (limit = 20) => apiClient.get(`/news/market?limit=${limit}`),
  ticker: (ticker: string) => apiClient.get(`/news/${ticker}`),
  sentiment: (ticker: string) => apiClient.get(`/news/sentiment/${ticker}`),
};

export const portfolioApi = {
  summary: () => apiClient.get("/portfolio/summary"),
  holdings: () => apiClient.get("/portfolio/holdings"),
  transactions: () => apiClient.get("/portfolio/transactions"),
  brokers: () => apiClient.get("/portfolio/brokers"),
  syncBroker: (id: string) => apiClient.post(`/portfolio/brokers/sync/${id}`),
  unlinkBroker: (id: string) => apiClient.delete(`/portfolio/brokers/${id}`),
};

export const screenerApi = {
  scan: (params: Record<string, unknown>) => apiClient.get("/screener/scan", { params }),
  metadata: () => apiClient.get("/screener/metadata"),
  watchlist: () => apiClient.get("/screener/watchlist"),
  addToWatchlist: (ticker: string) => apiClient.post(`/screener/watchlist/${ticker}`),
  removeFromWatchlist: (ticker: string) => apiClient.delete(`/screener/watchlist/${ticker}`),
};

export const marketsApi = {
  overview: () => apiClient.get("/markets/overview"),
  search: (q: string) => apiClient.get("/markets/search", { params: { q } }),
  searchContext: () => apiClient.get("/markets/search/context"),
  company: (symbol: string) => apiClient.get(`/markets/companies/${symbol}`),
  companyChart: (symbol: string, range: string) =>
    apiClient.get(`/markets/companies/${symbol}/chart`, { params: { range } }),
  companyNews: (symbol: string, limit = 10) =>
    apiClient.get(`/markets/companies/${symbol}/news`, { params: { limit } }),
  news: (params: {
    page?: number;
    limit?: number;
    category?: string;
    exchange?: string;
    sector?: string;
    marketCap?: string;
    sentiment?: string;
  }) => apiClient.get("/markets/news", { params }),
  watchlist: () => apiClient.get("/markets/watchlist"),
  addWatchlist: (payload: { symbol: string; exchange?: string; notes?: string }) =>
    apiClient.post("/markets/watchlist", payload),
  deleteWatchlist: (symbol: string) => apiClient.delete(`/markets/watchlist/${symbol}`),
  bookmarks: () => apiClient.get("/markets/bookmarks"),
  addBookmark: (payload: {
    articleId: string;
    title: string;
    sourceUrl: string;
    source: string;
    publishedAt: string;
  }) => apiClient.post("/markets/bookmarks", payload),
  deleteBookmark: (articleId: string) => apiClient.delete(`/markets/bookmarks/${articleId}`),
  alerts: () => apiClient.get("/markets/alerts"),
  addAlert: (payload: {
    symbol: string;
    exchange?: string;
    alertType: "price_above" | "price_below" | "pct_change";
    thresholdValue: number;
  }) => apiClient.post("/markets/alerts", payload),
  deleteAlert: (alertId: string) => apiClient.delete(`/markets/alerts/${alertId}`),
};

export const finsightApi = {
  ticker: (symbol: string) => apiClient.get(`/finsight/ticker/${symbol}`),
  sessions: (userId: string) => apiClient.get(`/finsight/sessions`, { params: { user_id: userId } }),
  history: (sessionId: string, userId: string) => apiClient.get(`/finsight/history/${sessionId}`, { params: { user_id: userId } }),
};
