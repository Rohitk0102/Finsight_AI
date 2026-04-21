"use client";

import Link from "next/link";
import { BarChart3, Lock } from "lucide-react";

export function MarketDisabledState() {
  return (
    <div className="market-shell rounded-[28px] p-6 md:p-10">
      <div className="market-card mx-auto max-w-2xl p-8 text-center">
        <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-white/[0.06] text-white">
          <Lock className="h-8 w-8" />
        </div>
        <p className="market-eyebrow justify-center">Feature Flag Off</p>
        <h1 className="mt-3 text-3xl font-semibold tracking-[-0.03em] text-white">
          Market Pulse is disabled in this environment
        </h1>
        <p className="mx-auto mt-3 max-w-xl text-sm text-slate-300">
          Set <code>NEXT_PUBLIC_FEATURE_MARKETS=true</code> to expose the dedicated
          market intelligence module and its live search, news impact, and company detail flows.
        </p>
        <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
          <Link href="/dashboard" className="btn-secondary border-white/10 text-white hover:bg-white/10">
            Back to Dashboard
          </Link>
          <div className="inline-flex items-center gap-2 rounded-full border border-emerald-400/25 bg-emerald-400/10 px-3 py-2 text-xs font-medium text-emerald-200">
            <BarChart3 className="h-4 w-4" />
            Route is guarded by a dedicated feature flag
          </div>
        </div>
      </div>
    </div>
  );
}
