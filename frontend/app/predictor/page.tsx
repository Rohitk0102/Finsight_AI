"use client";

import { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { stocksApi, predictApi } from "@/lib/api/client";
import { formatCurrency, formatChange, getSignalColor, getRiskColor } from "@/lib/utils";
import { Search, Loader2, ShieldAlert, TrendingUp, ChevronRight, Cpu } from "lucide-react";
import { toast } from "sonner";
import AccuracyDashboard from "@/components/predictor/AccuracyDashboard";

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
  const searchParams = useSearchParams();
  const initialTicker = searchParams.get("ticker");

  const [query,          setQuery]          = useState(initialTicker || "");
  const [riskProfile,    setRiskProfile]    = useState<RiskProfile>("moderate");
  const [horizon,        setHorizon]        = useState<Horizon>("medium");
  const [selectedSector, setSelectedSector] = useState<string>("All");
  const [searching,      setSearching]      = useState(false);
  const [predicting,     setPredicting]     = useState(false);
  const [results,        setResults]        = useState<Array<{ ticker: string; name: string; sector?: string }>>([]);
  const [prediction,     setPrediction]     = useState<Prediction | null>(null);
  const [selectedTicker, setSelectedTicker] = useState(initialTicker || "");
  const [showProfiler,   setShowProfiler]   = useState(false);
  const [profilerStep,   setProfilerStep]   = useState(1);
  const [profileAnswers, setProfileAnswers] = useState<Record<string, string>>({});

  const featuredStocks = [
    { ticker: "RELIANCE.NS", name: "Reliance Industries", sector: "Energy", profile: "moderate" },
    { ticker: "TCS.NS", name: "Tata Consultancy Services", sector: "Technology", profile: "conservative" },
    { ticker: "HDFCBANK.NS", name: "HDFC Bank", sector: "Finance", profile: "moderate" },
    { ticker: "INFY.NS", name: "Infosys", sector: "Technology", profile: "moderate" },
    { ticker: "ICICIBANK.NS", name: "ICICI Bank", sector: "Finance", profile: "moderate" },
    { ticker: "AAPL", name: "Apple Inc.", sector: "Technology", profile: "moderate" },
    { ticker: "MSFT", name: "Microsoft", sector: "Technology", profile: "conservative" },
    { ticker: "NVDA", name: "Nvidia", sector: "Technology", profile: "aggressive" },
    { ticker: "TSLA", name: "Tesla Inc.", sector: "Consumer", profile: "aggressive" },
    { ticker: "AMZN", name: "Amazon", sector: "Consumer", profile: "moderate" },
  ];

  const sectors = ["All", "Technology", "Finance", "Energy", "Consumer", "Healthcare"];

  const handleProfilerComplete = () => {
    // Logic to map answers to Risk and Horizon
    let risk: RiskProfile = "moderate";
    if (profileAnswers.risk === "high" || profileAnswers.goal === "growth") risk = "aggressive";
    if (profileAnswers.risk === "low") risk = "conservative";

    let h: Horizon = "medium";
    if (profileAnswers.time === "short") h = "short";
    if (profileAnswers.time === "long") h = "long";

    setRiskProfile(risk);
    setHorizon(h);
    setShowProfiler(false);
    toast.success("Profile updated! Showing your best matches.");
  };

  const profilerQuestions = [
    {
      id: "goal",
      question: "What is your primary investment goal?",
      options: [
        { label: "Wealth Growth", value: "growth", desc: "Maximise returns over time" },
        { label: "Capital Stability", value: "stability", desc: "Preserve wealth with low volatility" },
        { label: "Passive Income", value: "income", desc: "Focus on dividends and steady payouts" },
      ]
    },
    {
      id: "risk",
      question: "How do you feel about market volatility?",
      options: [
        { label: "Low", value: "low", desc: "I prefer steady, predictable returns" },
        { label: "Medium", value: "medium", desc: "I can handle some ups and downs" },
        { label: "High", value: "high", desc: "I'm okay with big swings for big gains" },
      ]
    },
    {
      id: "time",
      question: "What is your expected investment duration?",
      options: [
        { label: "Under 1 Year", value: "short", desc: "Quick tactical trades" },
        { label: "1 to 5 Years", value: "medium", desc: "Medium-term wealth building" },
        { label: "Over 5 Years", value: "long", desc: "Long-term compounding" },
      ]
    }
  ];

  const currentQuestion = profilerQuestions[profilerStep - 1];

  const handleSearch = async (overrideQuery?: string) => {
    const q = overrideQuery || query.trim();
    if (!q) return;
    setSearching(true);
    setPrediction(null);
    try {
      const res = await stocksApi.search(q);
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

  const filteredResults = selectedSector === "All" 
    ? results 
    : results.filter(r => r.sector?.toLowerCase().includes(selectedSector.toLowerCase()));

  const selectClass = "input-field appearance-none cursor-pointer";

  return (
    <div className="max-w-5xl relative">
      {/* Profiler Wizard Overlay */}
      {showProfiler && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm animate-fade-in">
          <div className="card-surface w-full max-w-lg p-8 shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 left-0 h-1 bg-primary transition-all duration-300" style={{ width: `${(profilerStep / profilerQuestions.length) * 100}%` }} />
            
            <button 
              onClick={() => setShowProfiler(false)} 
              className="absolute top-4 right-4 text-muted-foreground hover:text-foreground"
            >
              <Search className="h-5 w-5 rotate-45" />
            </button>

            <div className="mb-8">
              <span className="text-label-xs font-bold text-primary uppercase tracking-widest">
                Investor Profiler · Step {profilerStep} of {profilerQuestions.length}
              </span>
              <h2 className="text-2xl font-bold mt-2">{currentQuestion.question}</h2>
            </div>

            <div className="space-y-3 mb-8">
              {currentQuestion.options.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => {
                    setProfileAnswers({ ...profileAnswers, [currentQuestion.id]: opt.value });
                    if (profilerStep < profilerQuestions.length) {
                      setProfilerStep(profilerStep + 1);
                    } else {
                      // Final step logic
                      const finalAnswers = { ...profileAnswers, [currentQuestion.id]: opt.value };
                      
                      let risk: RiskProfile = "moderate";
                      if (finalAnswers.risk === "high" || finalAnswers.goal === "growth") risk = "aggressive";
                      if (finalAnswers.risk === "low") risk = "conservative";

                      let h: Horizon = "medium";
                      if (finalAnswers.time === "short") h = "short";
                      if (finalAnswers.time === "long") h = "long";

                      setRiskProfile(risk);
                      setHorizon(h);
                      setShowProfiler(false);
                      setProfilerStep(1);
                      toast.success(`Profile set to ${risk} / ${h}. Showing best matches.`);
                    }
                  }}
                  className={`w-full text-left p-4 rounded-xl border-2 transition-all hover:shadow-md group ${
                    profileAnswers[currentQuestion.id] === opt.value 
                    ? "border-primary bg-primary/5" 
                    : "border-border/50 hover:border-primary/30"
                  }`}
                >
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="font-bold text-[15px]">{opt.label}</p>
                      <p className="text-[12px] text-muted-foreground mt-0.5">{opt.desc}</p>
                    </div>
                    <ChevronRight className={`h-4 w-4 transition-transform ${profileAnswers[currentQuestion.id] === opt.value ? "text-primary" : "text-muted-foreground opacity-0 group-hover:opacity-100"}`} />
                  </div>
                </button>
              ))}
            </div>

            <div className="flex justify-between items-center text-muted-foreground text-[12px]">
              <button 
                onClick={() => profilerStep > 1 && setProfilerStep(profilerStep - 1)}
                disabled={profilerStep === 1}
                className="hover:text-foreground disabled:opacity-30 flex items-center gap-1"
              >
                <ChevronRight className="h-4 w-4 rotate-180" /> Previous
              </button>
              <span>Choose an option to continue</span>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between mb-6 gap-4">
        <div>
          <h1 className="text-page-title">Stock Predictor</h1>
          <p className="text-body-sm text-muted-foreground mt-0.5">
            AI ensemble prediction · LSTM + XGBoost + Prophet
          </p>
        </div>
        <button 
          onClick={() => { setShowProfiler(true); setProfilerStep(1); }}
          className="btn-outline text-[12px] h-9 px-4 flex items-center gap-2 bg-primary/5 border-primary/20 text-primary hover:bg-primary/10"
        >
          <Cpu className="h-3.5 w-3.5" />
          Personalise Predictor
        </button>
      </div>

      {/* Search card */}
      <div className="card-surface p-5 mb-4 animate-slide-in-up">
        <div className="flex flex-col md:flex-row gap-3 mb-4">
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
          <div className="flex gap-2">
            <select 
              value={selectedSector} 
              onChange={(e) => setSelectedSector(e.target.value)}
              className={`${selectClass} min-w-[140px]`}
            >
              {sectors.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
            <button
              onClick={() => handleSearch()}
              disabled={searching || !query.trim()}
              className="btn-primary px-5"
            >
              {searching ? <Loader2 className="h-4 w-4 animate-spin" /> : "Search"}
            </button>
          </div>
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
      {filteredResults.length > 0 && (
        <div className="card-surface mb-6 overflow-hidden animate-fade-in shadow-lg">
          <div className="px-5 py-2 bg-muted/30 text-label-xs font-semibold text-muted-foreground border-b border-border/50">
            SEARCH RESULTS
          </div>
          {filteredResults.map((r) => (
            <button
              key={r.ticker}
              onClick={() => handlePredict(r.ticker)}
              className="flex items-center justify-between w-full px-5 py-3.5 hover:bg-accent text-left transition-colors group border-b border-border/40 last:border-0"
            >
              <div>
                <span className="font-semibold text-[13px]">{r.ticker}</span>
                <span className="text-muted-foreground text-[13px] ml-2">{r.name}</span>
                {r.sector && (
                  <span className="ml-3 px-1.5 py-0.5 bg-primary/5 text-primary text-[10px] rounded font-medium">
                    {r.sector}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-1 text-[11px] font-medium group-hover:translate-x-0.5 transition-transform" style={{ color: "hsl(var(--primary))" }}>
                Predict <ChevronRight className="h-3 w-3" />
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Recommendations - Only show when no prediction and no results */}
      {!prediction && !predicting && results.length === 0 && (
        <div className="space-y-6 mb-8 animate-fade-in">
          <div>
            <h3 className="text-card-title font-semibold mb-3 flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-primary" />
              {Object.keys(profileAnswers).length > 0 ? "AI Recommendations For You" : "Featured Stocks to Predict"}
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {featuredStocks.map((s) => {
                const isMatch = s.profile === riskProfile;
                return (
                  <button
                    key={s.ticker}
                    onClick={() => handlePredict(s.ticker)}
                    className={`card-surface p-4 text-left transition-all hover:shadow-md group relative overflow-hidden ${
                      isMatch ? "border-primary/40 bg-primary/5" : "hover:border-primary/50"
                    }`}
                  >
                    {isMatch && (
                      <div className="absolute top-0 right-0 px-2 py-0.5 bg-primary text-[8px] font-bold text-white rounded-bl-lg uppercase tracking-tighter">
                        Best Match
                      </div>
                    )}
                    <p className={`font-bold text-[14px] group-hover:text-primary transition-colors ${isMatch ? "text-primary" : ""}`}>{s.ticker}</p>
                    <p className="text-[11px] text-muted-foreground truncate mb-2">{s.name}</p>
                    <div className="flex items-center gap-2">
                      <span className="px-1.5 py-0.5 bg-muted text-muted-foreground text-[9px] rounded font-semibold uppercase tracking-wider">
                        {s.sector}
                      </span>
                      {isMatch && (
                        <span className="text-[9px] font-bold text-primary flex items-center gap-0.5">
                          <Cpu className="h-2.5 w-2.5" /> High Signal
                        </span>
                      )}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="card-surface p-6 bg-gradient-to-br from-primary/5 to-transparent border-primary/10">
            <h3 className="font-semibold mb-2">How it works</h3>
            <p className="text-body-sm text-muted-foreground leading-relaxed">
              Our ensemble engine combines three distinct models: <strong>LSTM</strong> for deep sequence patterns, 
              <strong>XGBoost</strong> for technical relationships, and <strong>Prophet</strong> for seasonality. 
              Each prediction is augmented with real-time news sentiment and market regime analysis.
            </p>
          </div>
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

          <AccuracyDashboard />
        </div>
      )}

      {/* Empty state */}
      {!predicting && !prediction && results.length === 0 && (
        <div className="space-y-4 animate-fade-in">
          <div className="text-center py-20">
            <div
              className="kpi-icon-circle mx-auto mb-4"
              style={{ background: "hsl(var(--primary) / 0.08)", width: "64px", height: "64px" }}
            >
              <TrendingUp className="h-7 w-7 opacity-40" style={{ color: "hsl(var(--primary))" }} />
            </div>
            <p className="text-card-title text-muted-foreground">Search for a stock to get predictions</p>
          </div>
          <AccuracyDashboard />
        </div>
      )}
    </div>
  );
}
