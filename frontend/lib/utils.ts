import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(value: number, currency = "INR"): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatPercent(value: number): string {
  const sign = value >= 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}%`;
}

/** Returns ▲/▼ triangle + color class for percentage display per Figma spec */
export function formatChange(value: number): {
  symbol: "▲" | "▼";
  colorClass: string;
  text: string;
} {
  const isPositive = value >= 0;
  return {
    symbol: isPositive ? "▲" : "▼",
    colorClass: isPositive ? "text-[#22C55E]" : "text-[#EF4444]",
    text: `${Math.abs(value).toFixed(2)}%`,
  };
}

export function formatLargeNumber(value: number): string {
  if (value >= 1e12) return `₹${(value / 1e12).toFixed(2)}T`;
  if (value >= 1e9) return `₹${(value / 1e9).toFixed(2)}B`;
  if (value >= 1e7) return `₹${(value / 1e7).toFixed(2)}Cr`;
  if (value >= 1e5) return `₹${(value / 1e5).toFixed(2)}L`;
  return `₹${value.toFixed(2)}`;
}

export function getSignalColor(signal: string): string {
  if (signal === "BUY") return "text-[#22C55E]";
  if (signal === "SELL") return "text-[#EF4444]";
  return "text-[#f59e0b]";
}

export function getRiskColor(label: string): string {
  const map: Record<string, string> = {
    LOW: "text-[#22C55E]",
    MODERATE: "text-[#f59e0b]",
    HIGH: "text-orange-400",
    VERY_HIGH: "text-[#EF4444]",
  };
  return map[label] || "text-muted-foreground";
}
