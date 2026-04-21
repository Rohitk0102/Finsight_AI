"use client";

import {
  Area,
  Bar,
  CartesianGrid,
  Cell,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ChartPoint, ChartRange, IndicatorKey } from "@/lib/markets/types";
import { cn, formatCurrency } from "@/lib/utils";

interface MarketChartProps {
  points: ChartPoint[];
  range: ChartRange;
  mode: "line" | "candle";
  indicators: IndicatorKey[];
}

interface ChartTooltipProps {
  active?: boolean;
  payload?: Array<{ payload: ChartPoint }>;
  label?: string;
}

function CustomTooltip({ active, payload }: ChartTooltipProps) {
  if (!active || !payload?.length) return null;
  const row = payload[0].payload;
  return (
    <div className="rounded-2xl border border-white/10 bg-[#081018]/95 p-3 text-xs text-white shadow-2xl backdrop-blur-xl">
      <p className="mb-2 text-slate-400">{new Date(row.timestamp).toLocaleString("en-IN")}</p>
      <div className="grid grid-cols-2 gap-x-4 gap-y-1">
        <span>Open</span>
        <span className="text-right">{formatCurrency(row.open)}</span>
        <span>High</span>
        <span className="text-right">{formatCurrency(row.high)}</span>
        <span>Low</span>
        <span className="text-right">{formatCurrency(row.low)}</span>
        <span>Close</span>
        <span className="text-right">{formatCurrency(row.close)}</span>
        <span>Volume</span>
        <span className="text-right">{row.volume.toLocaleString("en-IN")}</span>
      </div>
    </div>
  );
}

export function MarketChart({ points, range, mode, indicators }: MarketChartProps) {
  const data = points.map((point) => ({
    ...point,
    label:
      range === "1D"
        ? new Date(point.timestamp).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })
        : new Date(point.timestamp).toLocaleDateString("en-IN", { day: "numeric", month: "short" }),
    bodyBase: Math.min(point.open, point.close),
    bodySize: Math.max(Math.abs(point.close - point.open), 0.01),
    candleTone: point.close >= point.open ? "#00C853" : "#F44336",
  }));

  const latest = points[points.length - 1];

  return (
    <div className="market-card p-4 md:p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="market-eyebrow">Market Structure</p>
          <h3 className="mt-2 text-xl font-semibold tracking-[-0.03em] text-white">Price + Technical Overlays</h3>
        </div>
        <div className="flex flex-wrap gap-2">
          {indicators.map((indicator) => (
            <span key={indicator} className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-200">
              {indicator}
            </span>
          ))}
        </div>
      </div>

      <div className="mt-5 h-[340px]">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ left: 0, right: 0, top: 8, bottom: 0 }}>
            <defs>
              <linearGradient id="marketArea" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#00C853" stopOpacity={0.32} />
                <stop offset="100%" stopColor="#00C853" stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
            <XAxis dataKey="label" stroke="#7E8A9A" tickLine={false} axisLine={false} minTickGap={24} />
            <YAxis stroke="#7E8A9A" tickLine={false} axisLine={false} width={78} tickFormatter={(value) => `₹${Math.round(value)}`} />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="volume" yAxisId={0} barSize={6} fill="rgba(148,163,184,0.12)" radius={[4, 4, 0, 0]} />
            {mode === "line" ? (
              <>
                <Area type="monotone" dataKey="close" stroke="#00C853" fill="url(#marketArea)" strokeWidth={2.4} />
                <Line type="monotone" dataKey="close" stroke="#7CF29A" strokeWidth={2} dot={false} />
              </>
            ) : (
              <>
                <Bar dataKey="bodyBase" stackId="candle" fill="transparent" />
                <Bar dataKey="bodySize" stackId="candle" radius={[3, 3, 0, 0]}>
                  {data.map((entry, index) => (
                    <Cell key={`candle-${index}`} fill={entry.candleTone} />
                  ))}
                </Bar>
                <Line type="monotone" dataKey="high" stroke="rgba(255,255,255,0.18)" dot={false} strokeWidth={1} />
                <Line type="monotone" dataKey="low" stroke="rgba(255,255,255,0.18)" dot={false} strokeWidth={1} />
              </>
            )}
            {indicators.includes("SMA") && <Line type="monotone" dataKey="sma20" stroke="#FFD166" dot={false} strokeWidth={1.6} />}
            {indicators.includes("EMA") && <Line type="monotone" dataKey="ema20" stroke="#7AA2FF" dot={false} strokeWidth={1.5} />}
            {indicators.includes("Bollinger") && (
              <>
                <Line type="monotone" dataKey="bbUpper" stroke="rgba(255,255,255,0.2)" dot={false} strokeDasharray="4 4" />
                <Line type="monotone" dataKey="bbLower" stroke="rgba(255,255,255,0.2)" dot={false} strokeDasharray="4 4" />
              </>
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-3">
        <div className="rounded-2xl border border-white/[0.08] bg-black/20 p-4">
          <p className="text-[11px] uppercase tracking-[0.24em] text-slate-500">RSI (14)</p>
          <p className={cn("mt-2 text-2xl font-semibold text-white", latest?.rsi14 && latest.rsi14 > 70 ? "text-rose-300" : latest?.rsi14 && latest.rsi14 < 30 ? "text-emerald-300" : "")}>
            {latest?.rsi14 ? latest.rsi14.toFixed(2) : "NA"}
          </p>
        </div>
        <div className="rounded-2xl border border-white/[0.08] bg-black/20 p-4">
          <p className="text-[11px] uppercase tracking-[0.24em] text-slate-500">MACD</p>
          <p className="mt-2 text-2xl font-semibold text-white">
            {latest?.macd ? latest.macd.toFixed(2) : "NA"}
          </p>
        </div>
        <div className="rounded-2xl border border-white/[0.08] bg-black/20 p-4">
          <p className="text-[11px] uppercase tracking-[0.24em] text-slate-500">MACD Signal</p>
          <p className="mt-2 text-2xl font-semibold text-white">
            {latest?.macdSignal ? latest.macdSignal.toFixed(2) : "NA"}
          </p>
        </div>
      </div>
    </div>
  );
}
