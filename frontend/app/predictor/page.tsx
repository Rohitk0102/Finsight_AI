"use client";

import { useState } from "react";
import { stocksApi, predictApi } from "@/lib/api/client";
import { formatCurrency, formatChange, getSignalColor, getRiskColor } from "@/lib/utils";
import { Search, Loader2, ShieldAlert, TrendingUp, ChevronRight, Cpu } from "lucide-react";
import { toast } from "sonner";

type RiskProfile = "conservative" | "moderate" | "aggressive";
type Horizon = "short" | "medium" | "long";

interface Prediction {
  ticker: string; current_price: number;
  predicted_1d: number; predicted_7d: number; predicted_30d: number;
  confidence: number; signal: string;
  risk_score: number; risk_label: string;
  sentiment_score: number; factors: string[];
  technicals: Record<string, number | null>;
}

export default function PredictorPage() {
  const [query,          setQuery]          = useState("");
  const [riskProfile,    setRiskProfile]    = useState<RiskProfile>("moderate");
  const [horizon,        setHorizon]        = useState<Horizon>("medium");
  const [searching,      setSearching]      = useState(false);
  const [predicting,     setPredicting]     = useState(false);
  const [results,        setResults]        = useState<Array<{ ticker: string; name: string }>>([]);
  const [prediction,     setPrediction]     = useState<Prediction | null>(null);
  const [selectedTicker, setSelectedTicker] = useState("");

  const handleSearch = async () => {
    if (!query.trim()) return;
    setSearching(true);
    try {
      const res = await stocksApi.search(query.trim());
      setResults(res.data);
    } catch {
      toast.error("Search failed");
    } finally {
      setSearching(false);
    }
  };

  const handlePredict = async (ticker: string) => {
    setSelectedTicker(ticker);
    setPredicting(true);
    setResults([]);
    setQuery(ticker);
    try {
      const res = await predictApi.predict(ticker, riskProfile, horizon);
      setPrediction(res.data);
    } catch {
      toast.error("Prediction failed. Please try again.");
    } finally {
      setPredicting(false);
    }
  };

  const selectClass = "input-field appearance-none cursor-pointer";

  return (
    <div className="max-w-5xl">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-page-title">Stock Predictor</h1>
        <p className="text-body-sm text-muted-foreground mt-0.5">
          AI ensemble prediction · LSTM + XGBoost + Prophet
        </p>
      </div>

      {/* Search card */}
      <div className="card-surface p-5 mb-4 animate-slide-in-up">
        <div className="flex gap-3 mb-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              placeholder="Search symbol (RELIANCE, AAPL, NIFTY…)"
              className="input-field pl-10"
            />
          </div>
          <button
            onClick={handleSearch}
            disabled={searching || !query.trim()}
            className="btn-primary px-5"
          >
            {searching ? <Loader2 className="h-4 w-4 animate-spin" /> : "Search"}
          </button>
        </div>

        <div className="flex flex-wrap gap-4">
          <div className="flex-1 min-w-32">
            <label className="text-label-xs text-muted-foreground mb-1.5 block font-medium">Risk Profile</label>
            <select value={riskProfile} onChange={(e) => setRiskProfile(e.target.value as RiskProfile)} className={selectClass}>
              <option value="conservative">Conservative</option>
              <option value="moderate">Moderate</option>
              <option value="aggressive">Aggressive</option>
            </select>
          </div>
          <div className="flex-1 min-w-32">
            <label className="text-label-xs text-muted-foreground mb-1.5 block font-medium">Time Horizon</label>
            <select value={horizon} onChange={(e) => setHorizon(e.target.value as Horizon)} className={selectClass}>
              <option value="short">Short (&lt;1 month)</option>
              <option value="medium">Medium (1–6 months)</option>
              <option value="long">Long (&gt;6 months)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Search results dropdown */}
      {results.length > 0 && (
        <div className="card-surface mb-4 overflow-hidden animate-fade-in">
          {results.map((r) => (
            <button
              key={r.ticker}
              onClick={() => handlePredict(r.ticker)}
              className="flex items-center justify-between w-full px-5 py-3.5 hover:bg-accent text-left transition-colors group"
              style={{ borderBottom: "1px solid hsl(var(--border))" }}
            >
              <div>
                <span className="font-semibold text-[13px]">{r.ticker}</span>
                <span className="text-muted-foreground text-[13px] ml-2">{r.name}</span>
              </div>
              <div className="flex items-center gap-1 text-[11px] font-medium group-hover:translate-x-0.5 transition-transform" style={{ color: "hsl(var(--primary))" }}>
                Predict <ChevronRight className="h-3 w-3" />
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Loading state */}
      {predicting && (
        <div className="card-surface flex flex-col items-center justify-center py-20 mb-4 animate-fade-in">
          <div
            className="kpi-icon-circle mb-4 animate-pulse-ring"
            style={{ background: "hsl(var(--primary) / 0.1)", width: "64px", height: "64px" }}
          >
            <Cpu className="h-7 w-7" style={{ color: "hsl(var(--primary))" }} />
          </div>
          <p className="text-card-title font-medium mb-1">Running ensemble models</p>
          <p className="text-body-sm text-muted-foreground">
            Analysing <strong>{selectedTicker}</strong> with LSTM + XGBoost + Prophet…
          </p>
        </div>
      )}

      {/* Prediction result */}
      {prediction && !predicting && (
        <div className="space-y-4 animate-slide-in-up">
          {/* Signal card */}
          <div className="card-surface p-5">
            <div className="flex items-start justify-between mb-4">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <h2 className="text-[22px] font-bold" style={{ letterSpacing: "-0.02em" }}>
                    {prediction.ticker}
                  </h2>
                  <span
                    className={`badge font-bold text-[12px] ${
                      prediction.signal === "BUY"  ? "badge-green" :
                      prediction.signal === "SELL" ? "badge-red"   : "badge-amber"
                    }`}
                  >
                    {prediction.signal}
                  </span>
                </div>
                <p className="text-[28px] font-bold" style={{ letterSpacing: "-0.02em" }}>
                  {formatCurrency(prediction.current_price)}
                </p>
              </div>
              <div className="text-right">
                <p className="text-label-xs text-muted-foreground mb-1">Confidence</p>
                <p
                  className="text-[28px] font-bold"
                  style={{ color: "hsl(var(--primary))", letterSpacing: "-0.02em" }}
                >
                  {(prediction.confidence * 100).toFixed(0)}%
                </p>
              </div>
            </div>

            {/* Confidence bar */}
            <div className="bg-muted rounded-full h-2 mb-5">
              <div
                className="rounded-full h-2 transition-all duration-700"
                style={{ width: `${prediction.confidence * 100}%`, background: "hsl(var(--primary))" }}
              />
            </div>

            {/* Price targets */}
            <div className="grid grid-cols-3 gap-3">
              {[
                { label: "1-Day",  value: prediction.predicted_1d },
                { label: "7-Day",  value: prediction.predicted_7d },
                { label: "30-Day", value: prediction.predicted_30d },
              ].map(({ label, value }) => {
                const pct = ((value - prediction.current_price) / prediction.current_price) * 100;
                const chg = formatChange(pct);
                return (
                  <div
                    key={label}
                    className="rounded-xl p-4 text-center"
                    style={{ background: "hsl(var(--muted) / 0.6)" }}
                  >
                    <p className="text-label-xs text-muted-foreground mb-1.5">{label} Target</p>
                    <p className="font-bold text-[14px]">{formatCurrency(value)}</p>
                    <p className={`text-label-xs font-semibold mt-0.5 ${chg.colorClass}`}>
                      {chg.symbol} {chg.text}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Risk & Factors */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="card-surface p-5">
              <div className="flex items-center gap-2 mb-4">
                <ShieldAlert className="h-4 w-4" style={{ color: "hsl(var(--primary))" }} />
                <h3 className="text-card-title font-semibold">Risk Assessment</h3>
              </div>
              <div className="space-y-3">
                {[
                  {
                    label: "Risk Score",
                    value: `${prediction.risk_score}/10`,
                    colorClass: getRiskColor(prediction.risk_label),
                  },
                  {
                    label: "Risk Level",
                    value: prediction.risk_label,
                    colorClass: getRiskColor(prediction.risk_label),
                  },
                  {
                    label: "News Sentiment",
                    value: `${prediction.sentiment_score >= 0 ? "Positive" : "Negative"} (${prediction.sentiment_score.toFixed(2)})`,
                    colorClass: prediction.sentiment_score >= 0 ? "text-[#22C55E]" : "text-[#EF4444]",
                  },
                ].map(({ label, value, colorClass }) => (
                  <div
                    key={label}
                    className="flex items-center justify-between py-2.5"
                    style={{ borderBottom: "1px solid hsl(var(--border) / 0.6)" }}
                  >
                    <span className="text-[13px] text-muted-foreground">{label}</span>
                    <span className={`text-[13px] font-semibold ${colorClass}`}>{value}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="card-surface p-5">
              <div className="flex items-center gap-2 mb-4">
                <TrendingUp className="h-4 w-4" style={{ color: "hsl(var(--primary))" }} />
                <h3 className="text-card-title font-semibold">Key Factors</h3>
              </div>
              <ul className="space-y-2.5">
                {prediction.factors.map((f, i) => (
                  <li key={i} className="flex items-start gap-2.5 text-[13px]">
                    <span
                      className="mt-1.5 w-1.5 h-1.5 rounded-full flex-shrink-0"
                      style={{ background: "hsl(var(--primary))" }}
                    />
                    <span className="text-muted-foreground leading-snug">{f}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Technicals */}
          <div className="card-surface p-5">
            <h3 className="text-card-title font-semibold mb-4">Technical Indicators</h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { key: "rsi",      label: "RSI" },
                { key: "macd",     label: "MACD" },
                { key: "ema_20",   label: "EMA 20" },
                { key: "ema_50",   label: "EMA 50" },
                { key: "atr",      label: "ATR" },
                { key: "stoch_k",  label: "Stoch K" },
                { key: "bb_upper", label: "BB Upper" },
                { key: "bb_lower", label: "BB Lower" },
              ].map(({ key, label }) => (
                <div
                  key={key}
                  className="rounded-xl p-3.5"
                  style={{ background: "hsl(var(--muted) / 0.6)" }}
                >
                  <p className="text-label-xs text-muted-foreground mb-1">{label}</p>
                  <p className="font-bold text-[14px]">
                    {prediction.technicals[key]?.toFixed(2) ?? "—"}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Empty state */}
      {!predicting && !prediction && results.length === 0 && (
        <div className="text-center py-20 animate-fade-in">
          <div
            className="kpi-icon-circle mx-auto mb-4"
            style={{ background: "hsl(var(--primary) / 0.08)", width: "64px", height: "64px" }}
          >
            <TrendingUp className="h-7 w-7 opacity-40" style={{ color: "hsl(var(--primary))" }} />
          </div>
          <p className="text-card-title text-muted-foreground">Search for a stock to get predictions</p>
        </div>
      )}
    </div>
  );
}
