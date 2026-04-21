"use client";

import { useEffect, useState } from "react";
import { portfolioApi, predictApi } from "@/lib/api/client";
import { formatCurrency, formatChange, getSignalColor, getRiskColor } from "@/lib/utils";
import {
  ArrowUpRight, RefreshCw, TrendingUp, Wallet,
  Activity, Plus, Download, Clock, ChevronRight,
} from "lucide-react";
import Link from "next/link";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
  PieChart, Pie,
} from "recharts";
import { toast } from "sonner";

/* ── Types ──────────────────────────────────────────────────────── */
interface PortfolioSummary {
  total_invested: number;
  total_current_value: number;
  total_unrealized_pnl: number;
  total_unrealized_pnl_pct: number;
  day_change: number;
  day_change_pct: number;
  holdings_count: number;
  brokers_connected: number;
  top_holdings: Array<{
    ticker: string; name: string; current_value: number;
    unrealized_pnl: number; unrealized_pnl_pct: number;
  }>;
}

/* ── Dummy/fallback chart data ───────────────────────────────────── */
const weeklyBarData = [
  { day: "S", value: 42 },
  { day: "M", value: 72 },
  { day: "T", value: 68 },
  { day: "W", value: 88 },
  { day: "T", value: 38 },
  { day: "F", value: 62 },
  { day: "S", value: 50 },
];

const pieColors = ["#16a34a", "#4ade80", "#86efac"];

const watchlistItems = [
  { emoji: "⚡", name: "RELIANCE",   due: "NSE · ₹2,847" },
  { emoji: "🏦", name: "HDFCBANK",  due: "NSE · ₹1,612" },
  { emoji: "💻", name: "INFY",       due: "NSE · ₹1,489" },
  { emoji: "🚜", name: "M&M",        due: "NSE · ₹2,056" },
  { emoji: "🔬", name: "SUNPHARMA", due: "NSE · ₹1,124" },
];

/* ── Stat Card ───────────────────────────────────────────────────── */
function StatCard({
  title, value, sub, trend, filled = false, delay = 0,
}: {
  title: string; value: string; sub?: string | null;
  trend?: string | null; filled?: boolean; delay?: number;
}) {
  return (
    <div
      className={`rounded-2xl p-5 animate-slide-in-up ${
        filled
          ? "bg-primary text-primary-foreground"
          : "card-surface"
      }`}
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="flex items-start justify-between mb-4">
        <p className={`text-[12px] font-medium ${filled ? "text-primary-foreground/70" : "text-muted-foreground"}`}>
          {title}
        </p>
        <div
          className={`w-7 h-7 rounded-lg flex items-center justify-center ${
            filled ? "bg-primary-foreground/20" : "bg-primary/10"
          }`}
        >
          <ArrowUpRight
            className={`h-3.5 w-3.5 ${filled ? "text-primary-foreground" : "text-primary"}`}
          />
        </div>
      </div>
      <p
        className={`text-[26px] font-bold leading-none tracking-tight mb-2 ${
          filled ? "text-primary-foreground" : "text-foreground"
        }`}
      >
        {value}
      </p>
      {(sub || trend) && (
        <p className={`text-[12px] flex items-center gap-1 ${filled ? "text-primary-foreground/70" : "text-muted-foreground"}`}>
          {trend && <TrendingUp className="h-3 w-3" />}
          {sub ?? trend}
        </p>
      )}
    </div>
  );
}

/* ── Custom Bar tooltip ──────────────────────────────────────────── */
function CustomBarTooltip({ active, payload, label }: any) {
  if (active && payload?.length) {
    return (
      <div className="bg-foreground text-background px-3 py-2 rounded-xl text-[12px] shadow-xl">
        <p className="opacity-60">{label}</p>
        <p className="font-bold text-green-400">{payload[0].value}%</p>
      </div>
    );
  }
  return null;
}

/* ── Main Page ───────────────────────────────────────────────────── */
export default function DashboardPage() {
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [analyses, setAnalyses] = useState<Array<{
    ticker: string; signal: string; confidence: number;
    risk_label: string; predicted_7d: number; current_price: number;
  }>>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [chartsReady, setChartsReady] = useState(false);

  useEffect(() => { fetchData(); }, []);
  useEffect(() => { setChartsReady(true); }, []);

  const fetchData = async (silent = false) => {
    if (!silent) setLoading(true);
    else setRefreshing(true);
    try {
      const [summaryRes, analysisRes] = await Promise.allSettled([
        portfolioApi.summary(),
        predictApi.portfolioAnalysis(),
      ]);
      if (summaryRes.status === "fulfilled") setSummary(summaryRes.value.data);
      if (analysisRes.status === "fulfilled") setAnalyses(analysisRes.value.data.analyses ?? []);
    } catch {
      toast.error("Failed to load dashboard data");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const pnlPositive = (summary?.total_unrealized_pnl ?? 0) >= 0;
  const dayPositive = (summary?.day_change ?? 0) >= 0;
  const pnlPct = summary?.total_unrealized_pnl_pct ?? 0;
  const dayPct = summary?.day_change_pct ?? 0;

  /* Portfolio pie data */
  const piePct = Math.abs(pnlPct).toFixed(1);
  const pieData = [
    { name: "Gains",   value: Math.max(0, pnlPct) },
    { name: "Invested",value: Math.max(5, 100 - Math.abs(pnlPct)) },
    { name: "Loss",    value: Math.max(0, -pnlPct) },
  ].filter(d => d.value > 0);

  /* Market status */
  const [clockTime, setClockTime] = useState<string>("");
  const [isMarketOpen, setIsMarketOpen] = useState(false);
  const [marketLabel, setMarketLabel] = useState("Market Closed");
  
  useEffect(() => {
    // Initialize on client side only
    const updateMarketStatus = () => {
      const now = new Date();
      const hour = now.getHours();
      const open = hour >= 9 && hour < 16;
      setIsMarketOpen(open);
      setMarketLabel(open ? "Market Open" : "Market Closed");
      setClockTime(now.toLocaleTimeString("en-IN", { 
        hour: "2-digit", 
        minute: "2-digit", 
        second: "2-digit" 
      }));
    };
    
    updateMarketStatus();
    const id = setInterval(updateMarketStatus, 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="max-w-[1400px] mx-auto space-y-5">

      {/* ── Page header ─────────────────────────────────────────── */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-page-title text-foreground">Dashboard</h1>
          <p className="text-[13px] text-muted-foreground mt-0.5">
            Monitor your portfolio, AI signals, and market insights.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link href="/predictor" className="btn-primary">
            <Plus className="h-3.5 w-3.5" />
            Run AI Analysis
          </Link>
          <button
            onClick={() => fetchData(true)}
            disabled={refreshing}
            className="btn-secondary"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? "animate-spin" : ""}`} />
            <span className="hidden sm:inline">Sync</span>
          </button>
        </div>
      </div>

      {/* ── Row 1: KPI stat cards ────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {loading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="card-surface rounded-2xl p-5 animate-pulse h-[120px]" />
          ))
        ) : (
          <>
            <StatCard
              filled
              title="Portfolio Value"
              value={formatCurrency(summary?.total_current_value ?? 0)}
              sub={`Invested ${formatCurrency(summary?.total_invested ?? 0)}`}
              delay={0}
            />
            <StatCard
              title="Total P&L"
              value={formatCurrency(summary?.total_unrealized_pnl ?? 0)}
              trend={`${pnlPositive ? "+" : ""}${pnlPct.toFixed(2)}% all time`}
              delay={60}
            />
            <StatCard
              title="Today's Change"
              value={formatCurrency(summary?.day_change ?? 0)}
              trend={`${dayPositive ? "+" : ""}${dayPct.toFixed(2)}% today`}
              delay={120}
            />
            <StatCard
              title="Holdings"
              value={String(summary?.holdings_count ?? 0)}
              sub={`${summary?.brokers_connected ?? 0} broker${(summary?.brokers_connected ?? 0) !== 1 ? "s" : ""} connected`}
              delay={180}
            />
          </>
        )}
      </div>

      {/* ── Row 2: Chart + Right Widgets ────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

        {/* Bar chart — col-span-2 */}
        <div className="lg:col-span-2 card-surface p-5">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-[15px] font-semibold text-foreground">Portfolio Analytics</h2>
            <div className="flex items-center gap-1.5 text-[12px] text-muted-foreground">
              <span className="w-2 h-2 rounded-full bg-primary inline-block" />
              Weekly Activity
            </div>
          </div>
          {chartsReady ? (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={weeklyBarData} barSize={32} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
                <XAxis
                  dataKey="day"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fontSize: 12, fill: "#9ca3af" }}
                />
                <YAxis
                  axisLine={false}
                  tickLine={false}
                  tick={{ fontSize: 11, fill: "#9ca3af" }}
                  domain={[0, 100]}
                />
                <Tooltip content={<CustomBarTooltip />} cursor={false} />
                <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                  {weeklyBarData.map((entry, index) => (
                    <Cell
                      key={index}
                      fill={entry.value === Math.max(...weeklyBarData.map(d => d.value))
                        ? "#15803d"
                        : "#bbf7d0"
                      }
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[200px] rounded-xl bg-muted animate-pulse" />
          )}
          <div className="flex items-center justify-between mt-3 pt-3 border-t border-border">
            <p className="text-[12px] text-muted-foreground">
              Average: <span className="font-semibold text-foreground">
                {(weeklyBarData.reduce((s, d) => s + d.value, 0) / weeklyBarData.length).toFixed(0)}%
              </span>
            </p>
            <p className="text-[12px] text-muted-foreground">
              Peak: <span className="font-semibold text-primary">
                {Math.max(...weeklyBarData.map(d => d.value))}%
              </span>
            </p>
          </div>
        </div>

        {/* Right column */}
        <div className="space-y-4">
          {/* AI Signal Alert */}
          <div className="card-surface p-5">
            <h2 className="text-[15px] font-semibold text-foreground mb-3">Next Market Event</h2>
            <div className="bg-muted rounded-xl p-4">
              <p className="text-[13px] font-semibold text-foreground">RBI Policy Meeting</p>
              <p className="text-[12px] text-muted-foreground mt-0.5">Time: 10:00 am – 12:00 pm</p>
              <Link
                href="/news"
                className="btn-primary mt-3 w-full justify-center py-2.5 text-[13px]"
              >
                <Activity className="h-3.5 w-3.5" />
                View Market News
              </Link>
            </div>
          </div>

          {/* Portfolio Progress donut */}
          <div className="card-surface p-5">
            <h2 className="text-[15px] font-semibold text-foreground mb-4">Portfolio Health</h2>
            <div className="flex items-center gap-4">
              <div className="relative flex-shrink-0">
                {chartsReady ? (
                  <PieChart width={90} height={90}>
                    <Pie
                      data={pieData.length ? pieData : [{ name: "Empty", value: 1 }]}
                      cx={40} cy={40}
                      innerRadius={28} outerRadius={42}
                      startAngle={90} endAngle={-270}
                      stroke="none"
                      dataKey="value"
                    >
                      {(pieData.length ? pieData : []).map((_, i) => (
                        <Cell key={i} fill={pieColors[i % pieColors.length]} />
                      ))}
                      {!pieData.length && <Cell fill="#e5e7eb" />}
                    </Pie>
                  </PieChart>
                ) : (
                  <div className="w-[90px] h-[90px] rounded-full bg-muted animate-pulse" />
                )}
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-[14px] font-bold text-foreground">
                    {Math.abs(pnlPct).toFixed(0)}%
                  </span>
                </div>
              </div>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-sm bg-green-600 flex-shrink-0" />
                  <span className="text-[12px] text-muted-foreground">Gain</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-sm bg-green-300 flex-shrink-0" />
                  <span className="text-[12px] text-muted-foreground">Invested</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-sm bg-green-100 flex-shrink-0" />
                  <span className="text-[12px] text-muted-foreground">Unrealised</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Row 3: Holdings + Watchlist + Market Status ──────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

        {/* Holdings / AI Analysis */}
        <div className="lg:col-span-2 card-surface">
          <div className="flex items-center justify-between px-5 py-4 border-b border-border">
            <h2 className="text-[15px] font-semibold text-foreground">
              {analyses.length > 0 ? "AI Portfolio Analysis" : "Top Holdings"}
            </h2>
            <Link
              href={analyses.length > 0 ? "/predictor" : "/portfolio"}
              className="flex items-center gap-1 text-[12px] text-muted-foreground hover:text-primary transition-colors"
            >
              View all <ChevronRight className="h-3.5 w-3.5" />
            </Link>
          </div>

          {loading ? (
            <div className="p-5 space-y-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="flex items-center gap-3 animate-pulse">
                  <div className="w-10 h-10 rounded-full bg-muted flex-shrink-0" />
                  <div className="flex-1 space-y-2">
                    <div className="h-3 bg-muted rounded w-1/3" />
                    <div className="h-2.5 bg-muted/60 rounded w-2/3" />
                  </div>
                  <div className="h-6 w-16 bg-muted rounded-full" />
                </div>
              ))}
            </div>
          ) : analyses.length > 0 ? (
            <div className="divide-y divide-border">
              {analyses.slice(0, 5).map((a, i) => {
                const changePct = ((a.predicted_7d - a.current_price) / a.current_price) * 100;
                const chg = formatChange(changePct);
                const initials = a.ticker.slice(0, 2);
                const colors = ["bg-blue-500", "bg-purple-500", "bg-orange-500", "bg-pink-500", "bg-teal-500"];
                return (
                  <div key={a.ticker} className="flex items-center gap-4 px-5 py-3.5 hover:bg-accent/50 transition-colors">
                    <div className={`w-10 h-10 rounded-full ${colors[i % colors.length]} flex items-center justify-center flex-shrink-0`}>
                      <span className="text-[12px] font-bold text-white">{initials}</span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-[13px] font-semibold text-foreground">{a.ticker}</p>
                      <p className="text-[12px] text-muted-foreground truncate">
                        7d target: {formatCurrency(a.predicted_7d)} · {a.risk_label} risk
                      </p>
                    </div>
                    <span
                      className={`px-2.5 py-1 rounded-full text-[11px] font-semibold ${
                        a.signal === "BUY"
                          ? "bg-green-500/10 text-green-600"
                          : a.signal === "SELL"
                          ? "bg-red-500/10 text-red-500"
                          : "bg-amber-500/10 text-amber-600"
                      }`}
                    >
                      {a.signal}
                    </span>
                  </div>
                );
              })}
            </div>
          ) : summary?.top_holdings && summary.top_holdings.length > 0 ? (
            <div className="divide-y divide-border">
              {summary.top_holdings.slice(0, 5).map((h, i) => {
                const chg = formatChange(h.unrealized_pnl_pct);
                const colors = ["bg-blue-500", "bg-purple-500", "bg-orange-500", "bg-pink-500", "bg-teal-500"];
                return (
                  <div key={h.ticker} className="flex items-center gap-4 px-5 py-3.5 hover:bg-accent/50 transition-colors">
                    <div className={`w-10 h-10 rounded-full ${colors[i % colors.length]} flex items-center justify-center flex-shrink-0`}>
                      <span className="text-[12px] font-bold text-white">{h.ticker.slice(0, 2)}</span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-[13px] font-semibold text-foreground">{h.ticker}</p>
                      <p className="text-[12px] text-muted-foreground truncate">
                        {h.name} · {formatCurrency(h.current_value)}
                      </p>
                    </div>
                    <span
                      className={`px-2.5 py-1 rounded-full text-[11px] font-semibold ${
                        h.unrealized_pnl_pct >= 0
                          ? "bg-green-500/10 text-green-600"
                          : "bg-red-500/10 text-red-500"
                      }`}
                    >
                      {chg.symbol}{chg.text}
                    </span>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-14 px-5 text-center">
              <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mb-3">
                <Wallet className="h-5 w-5 text-primary" />
              </div>
              <p className="text-[14px] font-semibold text-foreground mb-1">No holdings yet</p>
              <p className="text-[12px] text-muted-foreground mb-4">Connect a broker to sync your portfolio</p>
              <Link href="/settings" className="btn-primary px-5 py-2">
                Connect Broker
              </Link>
            </div>
          )}
        </div>

        {/* Right column: Watchlist + Market Status */}
        <div className="space-y-4">
          {/* Watchlist */}
          <div className="card-surface">
            <div className="flex items-center justify-between px-5 py-4 border-b border-border">
              <h2 className="text-[15px] font-semibold text-foreground">Watchlist</h2>
              <Link
                href="/screener"
                className="flex items-center gap-1 text-[12px] text-muted-foreground hover:text-primary transition-colors"
              >
                <Plus className="h-3 w-3" /> Add
              </Link>
            </div>
            <div className="divide-y divide-border">
              {watchlistItems.map((item, i) => (
                <div key={item.name} className="flex items-center gap-3 px-5 py-3 hover:bg-accent/50 transition-colors">
                  <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center text-[14px] flex-shrink-0">
                    {item.emoji}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-[13px] font-semibold text-foreground">{item.name}</p>
                    <p className="text-[11px] text-muted-foreground">{item.due}</p>
                  </div>
                  {i === 0 && (
                    <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-primary/10 text-primary">
                      Watch
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Market Status */}
          <div className="rounded-2xl p-5 text-white" style={{ background: "#0f1912" }}>
            <div className="flex items-center gap-2 mb-3">
              <Clock className="h-4 w-4 text-white/40" />
              <span className="text-[13px] font-medium text-white/60">Market Status</span>
            </div>
            <p className="text-[28px] font-bold tracking-tight font-mono leading-none mb-3" suppressHydrationWarning>
              {clockTime || "00:00:00"}
            </p>
            <div className="flex items-center gap-2">
              <span
                className={`w-2 h-2 rounded-full ${isMarketOpen ? "bg-green-400 animate-pulse" : "bg-red-400"}`}
              />
              <span className={`text-[12px] font-medium ${isMarketOpen ? "text-green-400" : "text-red-400"}`}>
                {marketLabel}
              </span>
            </div>
            <div className="mt-3 pt-3 border-t border-white/10 grid grid-cols-2 gap-2">
              <div>
                <p className="text-[10px] text-white/40 uppercase tracking-wide">Opens</p>
                <p className="text-[12px] font-semibold text-white/80">9:15 AM IST</p>
              </div>
              <div>
                <p className="text-[10px] text-white/40 uppercase tracking-wide">Closes</p>
                <p className="text-[12px] font-semibold text-white/80">3:30 PM IST</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
