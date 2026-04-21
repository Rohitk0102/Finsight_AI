"use client";

import { useEffect, useState } from "react";
import { portfolioApi } from "@/lib/api/client";
import { formatCurrency, formatChange } from "@/lib/utils";
import { RefreshCw, Loader2, Plus, Unlink, Briefcase, ArrowUpRight } from "lucide-react";
import { toast } from "sonner";
import Link from "next/link";

interface Holding {
  ticker: string; name: string; quantity: number;
  average_price: number; current_price: number;
  current_value: number; invested_value: number;
  unrealized_pnl: number; unrealized_pnl_pct: number;
  day_change: number; day_change_pct: number;
}
interface Broker {
  id: string; broker: string; display_name: string;
  is_active: boolean; last_synced_at: string;
}

const brokerColors: Record<string, string> = {
  zerodha:   "#387ED1",
  upstox:    "#7B68EE",
  angelone:  "#E85D04",
  groww:     "#00D09C",
};

export default function PortfolioPage() {
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [brokers,  setBrokers]  = useState<Broker[]>([]);
  const [loading,  setLoading]  = useState(true);
  const [syncing,  setSyncing]  = useState<string | null>(null);

  useEffect(() => { fetchAll(); }, []);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [h, b] = await Promise.all([portfolioApi.holdings(), portfolioApi.brokers()]);
      setHoldings(h.data);
      setBrokers(b.data);
    } catch {
      toast.error("Failed to load portfolio");
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async (id: string) => {
    setSyncing(id);
    try {
      const res = await portfolioApi.syncBroker(id);
      toast.success(`Synced ${res.data.holdings_synced} holdings`);
      await fetchAll();
    } catch {
      toast.error("Sync failed");
    } finally {
      setSyncing(null);
    }
  };

  const handleUnlink = async (id: string) => {
    try {
      await portfolioApi.unlinkBroker(id);
      toast.success("Broker unlinked");
      setBrokers((b) => b.filter((x) => x.id !== id));
    } catch {
      toast.error("Failed to unlink");
    }
  };

  if (loading) return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="text-center">
        <Loader2 className="h-8 w-8 animate-spin mx-auto mb-2" style={{ color: "hsl(var(--primary))" }} />
        <p className="text-body-sm text-muted-foreground">Loading portfolio…</p>
      </div>
    </div>
  );

  const tableHeaders = ["Stock", "Qty", "Avg Price", "Current", "Value", "P&L", "Day"];

  return (
    <div className="max-w-7xl">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-page-title">Portfolio</h1>
          <p className="text-body-sm text-muted-foreground mt-0.5">
            {holdings.length} holdings · {brokers.length} broker{brokers.length !== 1 ? "s" : ""} connected
          </p>
        </div>
        <button onClick={fetchAll} className="btn-secondary flex items-center gap-2 px-3 py-2">
          <RefreshCw className="h-3.5 w-3.5" />
          <span className="hidden sm:inline text-[13px]">Refresh</span>
        </button>
      </div>

      {/* Brokers */}
      <section className="mb-8 animate-slide-in-up">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-card-title font-semibold">Connected Brokers</h2>
          <Link
            href="/settings"
            className="flex items-center gap-1 text-[11px] font-medium hover:text-primary transition-colors text-muted-foreground"
          >
            <Plus className="h-3.5 w-3.5" /> Add Broker
          </Link>
        </div>

        {brokers.length === 0 ? (
          <div className="card-surface p-8 text-center border-dashed border-2 border-border">
            <Briefcase className="h-8 w-8 mx-auto mb-3 opacity-20" style={{ color: "hsl(var(--primary))" }} />
            <p className="text-body-sm text-muted-foreground mb-1">No brokers connected yet</p>
            <Link href="/settings" className="text-[13px] font-medium hover:underline" style={{ color: "hsl(var(--primary))" }}>
              Connect your first broker →
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {brokers.map((b, i) => {
              const color = brokerColors[b.broker] || "hsl(var(--primary))";
              return (
                <div
                  key={b.id}
                  className={`card-surface p-5 animate-slide-in-up`}
                  style={{ animationDelay: `${i * 60}ms` }}
                >
                  {/* Header */}
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div
                        className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 text-white font-bold text-[13px]"
                        style={{ background: color + "22", color }}
                      >
                        {b.broker.slice(0, 2).toUpperCase()}
                      </div>
                      <div>
                        <p className="font-semibold text-[14px] capitalize">{b.broker.replace("_", " ")}</p>
                        <p className="text-label-xs text-muted-foreground">{b.display_name}</p>
                      </div>
                    </div>
                    <span className={`badge ${b.is_active ? "badge-green" : "bg-muted text-muted-foreground"}`}>
                      {b.is_active ? "Active" : "Inactive"}
                    </span>
                  </div>

                  {b.last_synced_at && (
                    <p className="text-label-xs text-muted-foreground mb-4">
                      Last synced: {new Date(b.last_synced_at).toLocaleString("en-IN")}
                    </p>
                  )}

                  <div className="flex gap-2">
                    <button
                      onClick={() => handleSync(b.id)}
                      disabled={syncing === b.id}
                      className="flex items-center gap-1.5 text-label-xs font-medium px-3 py-1.5 rounded-lg transition-colors disabled:opacity-50"
                      style={{ background: "hsl(var(--primary) / 0.1)", color: "hsl(var(--primary))" }}
                    >
                      {syncing === b.id
                        ? <Loader2 className="h-3 w-3 animate-spin" />
                        : <RefreshCw className="h-3 w-3" />
                      }
                      Sync
                    </button>
                    <button
                      onClick={() => handleUnlink(b.id)}
                      className="flex items-center gap-1.5 text-label-xs font-medium px-3 py-1.5 rounded-lg transition-colors hover:bg-red-500/10 hover:text-red-500 text-muted-foreground border border-border"
                    >
                      <Unlink className="h-3 w-3" /> Unlink
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>

      {/* Holdings table */}
      <section className="animate-slide-in-up delay-150">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-card-title font-semibold">
            All Holdings
            <span className="ml-2 badge badge-primary">{holdings.length}</span>
          </h2>
          {holdings.length > 0 && (
            <Link href="/screener" className="flex items-center gap-1 text-[11px] text-muted-foreground hover:text-primary transition-colors">
              Screener <ArrowUpRight className="h-3 w-3" />
            </Link>
          )}
        </div>

        {holdings.length === 0 ? (
          <div className="card-surface p-10 text-center">
            <p className="text-body-sm text-muted-foreground">No holdings to show. Sync your broker accounts.</p>
          </div>
        ) : (
          <div className="card-surface overflow-x-auto">
            <table className="w-full text-body-sm min-w-[700px] table-rows">
              <thead>
                <tr style={{ borderBottom: "1px solid hsl(var(--border))" }}>
                  {tableHeaders.map((h) => (
                    <th
                      key={h}
                      className={`px-5 py-3 text-label-xs text-muted-foreground font-medium ${
                        h === "Stock" ? "text-left" : "text-right"
                      }`}
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {holdings.map((h) => {
                  const pnl = formatChange(h.unrealized_pnl_pct);
                  const day = formatChange(h.day_change_pct);
                  return (
                    <tr key={h.ticker}>
                      <td className="px-5 py-3.5">
                        <p className="font-semibold text-[13px]">{h.ticker}</p>
                        <p className="text-label-xs text-muted-foreground truncate max-w-[120px]">{h.name}</p>
                      </td>
                      <td className="px-5 py-3.5 text-right text-[13px]">{h.quantity}</td>
                      <td className="px-5 py-3.5 text-right text-[13px]">{formatCurrency(h.average_price)}</td>
                      <td className="px-5 py-3.5 text-right text-[13px]">{formatCurrency(h.current_price)}</td>
                      <td className="px-5 py-3.5 text-right font-semibold text-[13px]">{formatCurrency(h.current_value)}</td>
                      <td className={`px-5 py-3.5 text-right text-[13px] font-semibold ${pnl.colorClass}`}>
                        {formatCurrency(h.unrealized_pnl)}
                        <br />
                        <span className="text-label-xs font-medium">{pnl.symbol} {pnl.text}</span>
                      </td>
                      <td className={`px-5 py-3.5 text-right text-[13px] font-semibold ${day.colorClass}`}>
                        {day.symbol} {day.text}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
