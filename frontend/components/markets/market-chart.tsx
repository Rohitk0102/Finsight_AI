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
  ReferenceLine,
} from "recharts";
import { useState } from "react";
import type { ChartPoint, ChartRange, IndicatorKey } from "@/lib/markets/types";
import { cn, formatCurrency } from "@/lib/utils";

interface MarketChartProps {
  points: ChartPoint[];
  range: ChartRange;
  mode: "line" | "candle";
  indicators: IndicatorKey[];
  onHover?: (data: ChartPoint | null) => void;
}

interface ChartTooltipProps {
  active?: boolean;
  payload?: any[];
  label?: string;
  onHover?: (data: ChartPoint | null) => void;
}

function CustomTooltip({ active, payload, label, onHover }: ChartTooltipProps) {
  // We use a useEffect-like pattern via render logic to pass data back up if needed, 
  // but for now, just the visual tooltip.
  if (!active || !payload?.length) {
    return null;
  }
  
  const data = payload[0].payload as ChartPoint;
  
  return (
    <div className="rounded-xl border border-white/10 bg-[#0B121B]/95 p-3 text-[11px] text-white shadow-2xl backdrop-blur-md min-w-[140px]">
      <p className="mb-2 text-slate-500 font-bold border-b border-white/5 pb-1">
        {new Date(data.timestamp).toLocaleString("en-IN", {
          day: "2-digit",
          month: "short",
          hour: "2-digit",
          minute: "2-digit"
        })}
      </p>
      <div className="space-y-1.5">
        <div className="flex justify-between gap-4">
          <span className="text-slate-400 font-medium">O</span>
          <span className="font-mono">{data.open.toFixed(2)}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-slate-400 font-medium">H</span>
          <span className="text-emerald-400 font-mono">{data.high.toFixed(2)}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-slate-400 font-medium">L</span>
          <span className="text-rose-400 font-mono">{data.low.toFixed(2)}</span>
        </div>
        <div className="flex justify-between gap-4 border-t border-white/5 pt-1 mt-1">
          <span className="text-slate-300 font-bold">C</span>
          <span className="font-bold font-mono text-[13px]">{data.close.toFixed(2)}</span>
        </div>
      </div>
    </div>
  );
}

/**
 * Custom Candlestick component for high-accuracy rendering
 */
const Candle = (props: any) => {
  const { x, width, payload, yAxis } = props;
  if (!yAxis) return null;
  
  const { open, close, high, low, candleColor } = payload;
  const scale = yAxis.scale;
  
  const cx = x + width / 2;
  const yHigh = scale(high);
  const yLow = scale(low);
  const yOpen = scale(open);
  const yClose = scale(close);
  
  const bodyTop = Math.min(yOpen, yClose);
  const bodyHeight = Math.max(Math.abs(yOpen - yClose), 1);

  return (
    <g>
      <line 
        x1={cx} 
        y1={yHigh} 
        x2={cx} 
        y2={yLow} 
        stroke={candleColor} 
        strokeWidth={1} 
      />
      <rect 
        x={x + width * 0.15} 
        y={bodyTop} 
        width={width * 0.7} 
        height={bodyHeight} 
        fill={candleColor} 
        rx={0.5} 
      />
    </g>
  );
};

export function MarketChart({ points, range, mode, indicators, onHover }: MarketChartProps) {
  const [hoveredData, setHoveredData] = useState<ChartPoint | null>(null);

  if (!points || points.length === 0) {
    return (
      <div className="flex h-[400px] items-center justify-center rounded-3xl border border-white/5 bg-white/[0.02] text-slate-500">
        No chart data available
      </div>
    );
  }

  // Calculate if the overall period is up or down to set line color
  const firstPrice = points[0].close;
  const lastPrice = points[points.length - 1].close;
  const isPeriodUp = lastPrice >= firstPrice;
  const mainColor = isPeriodUp ? "#00D09C" : "#EB5B3C"; // Groww-inspired colors

  const data = points.map((point) => ({
    ...point,
    label:
      range === "1D"
        ? new Date(point.timestamp).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })
        : new Date(point.timestamp).toLocaleDateString("en-IN", { day: "numeric", month: "short" }),
    // For candlestick hack:
    candleHigh: point.high,
    candleLow: point.low,
    candleOpen: point.open,
    candleClose: point.close,
    candleColor: point.close >= point.open ? "#00D09C" : "#EB5B3C",
    // We use a transparent bar to offset the candle body
    candleBottom: Math.min(point.open, point.close),
    candleHeight: Math.max(Math.abs(point.close - point.open), 0.1), // Ensure at least a tiny sliver
  }));

  const minPrice = Math.min(...points.map(p => p.low));
  const maxPrice = Math.max(...points.map(p => p.high));
  const latest = points[points.length - 1];

  return (
    <div className="relative">
      <div className="h-[400px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart 
            data={data} 
            margin={{ left: 0, right: 0, top: 10, bottom: 0 }}
            onMouseMove={(e: any) => {
              if (e.activePayload) {
                const hovered = e.activePayload[0].payload;
                setHoveredData(hovered);
                onHover?.(hovered);
              }
            }}
            onMouseLeave={() => {
              setHoveredData(null);
              onHover?.(null);
            }}
          >
            <defs>
              <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={mainColor} stopOpacity={0.2} />
                <stop offset="95%" stopColor={mainColor} stopOpacity={0} />
              </linearGradient>
            </defs>
            
            <CartesianGrid 
              strokeDasharray="3 3" 
              stroke="rgba(255,255,255,0.03)" 
              vertical={false} 
            />
            
            <XAxis 
              dataKey="label" 
              stroke="#475569" 
              tick={{ fontSize: 10, fontWeight: 600 }}
              tickLine={false} 
              axisLine={false} 
              minTickGap={40}
              dy={10}
            />
            
            <YAxis 
              orientation="right"
              stroke="#475569" 
              tick={{ fontSize: 10, fontWeight: 700 }}
              tickLine={false} 
              axisLine={false} 
              domain={['auto', 'auto']}
              tickFormatter={(val) => val.toLocaleString("en-IN", { maximumFractionDigits: 1 })}
              width={55}
            />

            <Tooltip 
              content={<CustomTooltip />} 
              cursor={{ stroke: "rgba(255,255,255,0.2)", strokeWidth: 1, strokeDasharray: "4 4" }}
              isAnimationActive={false}
              offset={-100}
            />

            {/* Linear Area Chart (More accurate than monotone) */}
            {mode === "line" && (
              <Area
                type="linear"
                dataKey="close"
                stroke={mainColor}
                strokeWidth={2}
                fill="url(#colorPrice)"
                isAnimationActive={true}
                animationDuration={800}
              />
            )}

            {/* High-Accuracy Custom Candlesticks */}
            {mode === "candle" && (
              <>
                {/* Hidden components to force YAxis domain to include high/low extent */}
                <Line dataKey="high" stroke="none" dot={false} isAnimationActive={false} />
                <Line dataKey="low" stroke="none" dot={false} isAnimationActive={false} />
                <Bar
                  dataKey="close"
                  isAnimationActive={false}
                  shape={<Candle />}
                />
              </>
            )}

            {/* Indicators */}
            {indicators.includes("SMA") && (
              <Line type="linear" dataKey="sma20" stroke="#F59E0B" dot={false} strokeWidth={1.5} opacity={0.8} isAnimationActive={false} />
            )}
            {indicators.includes("EMA") && (
              <Line type="linear" dataKey="ema20" stroke="#3B82F6" dot={false} strokeWidth={1.5} opacity={0.8} isAnimationActive={false} />
            )}
            {indicators.includes("MACD") && (
              <Line type="linear" dataKey="macd" stroke="#D946EF" dot={false} strokeWidth={1.5} opacity={0.7} isAnimationActive={false} />
            )}
            {indicators.includes("Bollinger") && (
              <>
                <Line type="linear" dataKey="bbUpper" stroke="#6366F1" dot={false} strokeWidth={1} strokeDasharray="3 3" opacity={0.4} />
                <Line type="linear" dataKey="bbLower" stroke="#6366F1" dot={false} strokeWidth={1} strokeDasharray="3 3" opacity={0.4} />
              </>
            )}


            {/* Reference line for latest price */}
            {!hoveredData && (
              <ReferenceLine 
                y={latest.close} 
                stroke={mainColor} 
                strokeDasharray="3 3" 
                label={{ 
                  position: "right", 
                  value: latest.close.toFixed(1), 
                  fill: mainColor, 
                  fontSize: 10,
                  fontWeight: "bold"
                }} 
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Accuracy Footer */}
      <div className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-4 animate-fade-in">
        <StatItem label="Range High" value={maxPrice} color="text-emerald-400" />
        <StatItem label="Range Low" value={minPrice} color="text-rose-400" />
        <StatItem label="Volume" value={latest.volume} isLarge />
        <StatItem label="RSI (14)" value={latest.rsi14} />
      </div>
    </div>
  );
}

function StatItem({ label, value, color, isLarge }: { label: string; value: number | undefined | null; color?: string; isLarge?: boolean }) {
  if (value === undefined || value === null) return null;
  return (
    <div className="bg-white/5 rounded-2xl p-4 border border-white/5 hover:bg-white/[0.08] transition-colors">
      <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-1">{label}</p>
      <p className={cn("text-lg font-bold", color || "text-white")}>
        {isLarge ? value.toLocaleString("en-IN") : value.toFixed(2)}
      </p>
    </div>
  );
}
