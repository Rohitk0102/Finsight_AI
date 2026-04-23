"use client";

import { useEffect, useState } from "react";
import { predictApi } from "@/lib/api/client";
import { Loader2, Target, BarChart3, Info } from "lucide-react";

interface AccuracyMetric {
  horizon_days: number;
  overall_hit_rate: number | null;
  overall_avg_mape: number | null;
  total_samples: number;
  ticker_count: number;
}

export default function AccuracyDashboard() {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<Record<string, AccuracyMetric>>({});

  useEffect(() => {
    async function fetchData() {
      try {
        const res = await predictApi.getAccuracySummary();
        setData(res.data.horizons || {});
      } catch (err) {
        console.error("Failed to fetch accuracy summary:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="card-surface p-8 flex items-center justify-center">
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground mr-2" />
        <span className="text-body-sm text-muted-foreground">Loading model metrics...</span>
      </div>
    );
  }

  const horizons = Object.values(data).sort((a, b) => a.horizon_days - b.horizon_days);

  if (horizons.length === 0) {
    return null;
  }

  return (
    <div className="card-surface p-5 animate-fade-in">
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-2">
          <Target className="h-4 w-4 text-primary" />
          <h3 className="text-card-title font-semibold">Model Accuracy Performance</h3>
        </div>
        <div className="group relative">
          <Info className="h-4 w-4 text-muted-foreground cursor-help" />
          <div className="absolute right-0 top-6 w-64 p-3 bg-popover text-popover-foreground text-[11px] rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50 border border-border">
            <p className="font-semibold mb-1">Metrics Explained:</p>
            <ul className="space-y-1 list-disc pl-3">
              <li><strong>Hit Rate:</strong> % of predictions where the price direction (Up/Down) was correct.</li>
              <li><strong>MAPE:</strong> Mean Absolute Percentage Error. Lower is better.</li>
              <li>Calculated daily via rolling 30-day backtest.</li>
            </ul>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {horizons.map((h) => (
          <div key={h.horizon_days} className="rounded-xl p-4 bg-muted/40 border border-border/40">
            <p className="text-label-xs text-muted-foreground mb-3 font-medium uppercase tracking-wider">
              {h.horizon_days}-Day Horizon
            </p>
            
            <div className="space-y-4">
              <div>
                <div className="flex justify-between items-end mb-1.5">
                  <span className="text-[12px] text-muted-foreground">Hit Rate</span>
                  <span className="text-[15px] font-bold text-primary">
                    {h.overall_hit_rate ? `${(h.overall_hit_rate * 100).toFixed(1)}%` : "N/A"}
                  </span>
                </div>
                <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-primary transition-all duration-1000" 
                    style={{ width: `${(h.overall_hit_rate || 0) * 100}%` }}
                  />
                </div>
              </div>

              <div className="flex justify-between items-center py-2 border-t border-border/30">
                <div className="flex items-center gap-1.5">
                  <BarChart3 className="h-3.5 w-3.5 text-muted-foreground" />
                  <span className="text-[12px] text-muted-foreground">Avg. Error (MAPE)</span>
                </div>
                <span className="text-[13px] font-semibold">
                  {h.overall_avg_mape ? `${h.overall_avg_mape.toFixed(2)}%` : "N/A"}
                </span>
              </div>

              <div className="text-[11px] text-muted-foreground text-center mt-2 opacity-60">
                Based on {h.total_samples.toLocaleString()} samples across {h.ticker_count} tickers
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
