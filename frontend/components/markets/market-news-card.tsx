"use client";

import Link from "next/link";
import { Bookmark, ExternalLink, TrendingDown, TrendingUp, Waves } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { cn } from "@/lib/utils";
import type { EnrichedNewsArticle } from "@/lib/markets/types";

interface MarketNewsCardProps {
  article: EnrichedNewsArticle;
  onToggleBookmark?: (article: EnrichedNewsArticle) => void;
}

function sentimentTone(sentiment: EnrichedNewsArticle["sentimentLabel"]) {
  if (sentiment === "bullish") {
    return {
      label: "Bullish",
      className: "bg-emerald-400/[0.12] text-emerald-300 border-emerald-400/20",
      icon: TrendingUp,
    };
  }
  if (sentiment === "bearish") {
    return {
      label: "Bearish",
      className: "bg-rose-500/[0.12] text-rose-300 border-rose-500/20",
      icon: TrendingDown,
    };
  }
  return {
    label: "Neutral",
    className: "bg-amber-400/[0.12] text-amber-200 border-amber-400/20",
    icon: Waves,
  };
}

export function MarketNewsCard({ article, onToggleBookmark }: MarketNewsCardProps) {
  const tone = sentimentTone(article.sentimentLabel);
  const ToneIcon = tone.icon;

  return (
    <article className="market-card p-4 md:p-5 news-virtual-item">
      <div className="flex items-start gap-3">
        <div className="flex-1">
          <div className="flex flex-wrap items-center gap-2 text-[11px] uppercase tracking-[0.24em] text-slate-400">
            <span>{article.source}</span>
            <span>{formatDistanceToNow(new Date(article.publishedAt), { addSuffix: true })}</span>
            <span className="rounded-full border border-white/10 px-2 py-1 text-[10px] tracking-[0.2em] text-slate-300">
              {article.category.replace("_", " ")}
            </span>
          </div>
          <h3 className="mt-3 text-lg font-semibold leading-tight text-white">
            {article.title}
          </h3>
          <p className="mt-2 text-sm leading-6 text-slate-300">
            {article.aiSummary}
          </p>
        </div>
        <button
          onClick={() => onToggleBookmark?.(article)}
          className={cn(
            "rounded-xl border p-2 transition",
            article.bookmarked
              ? "border-emerald-400/30 bg-emerald-400/[0.12] text-emerald-200"
              : "border-white/10 bg-white/5 text-slate-300 hover:bg-white/10"
          )}
          aria-label="Toggle bookmark"
        >
          <Bookmark className="h-4 w-4" />
        </button>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <div className="rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-white">
          Impact Score <span className="ml-1 font-semibold text-emerald-300">{article.impactScore}/100</span>
        </div>
        <div className={cn("inline-flex items-center gap-1 rounded-full border px-3 py-1.5 text-xs", tone.className)}>
          <ToneIcon className="h-3.5 w-3.5" />
          {tone.label}
        </div>
        <Link
          href={article.sourceUrl}
          target="_blank"
          className="inline-flex items-center gap-1 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-slate-200 transition hover:bg-white/10"
        >
          Open source
          <ExternalLink className="h-3.5 w-3.5" />
        </Link>
      </div>

      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <div>
          <p className="text-[11px] uppercase tracking-[0.24em] text-slate-500">Affected Companies</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {article.affectedCompanies.map((company) => (
              <Link
                key={`${article.id}-${company.displaySymbol}`}
                href={`/markets/${company.displaySymbol}`}
                className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-black/20 px-3 py-1.5 text-xs text-white transition hover:border-emerald-400/30 hover:bg-emerald-400/10"
              >
                <span>{company.displaySymbol}</span>
                <span className="text-slate-400">{company.direction === "up" ? "↑" : company.direction === "down" ? "↓" : "→"}</span>
                <span className="text-slate-300">{company.impactLevel}</span>
              </Link>
            ))}
          </div>
        </div>
        <div>
          <p className="text-[11px] uppercase tracking-[0.24em] text-slate-500">Sector Ripple</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {article.sectorRipple.map((sector) => (
              <span
                key={`${article.id}-${sector.sector}`}
                className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-slate-200"
              >
                {sector.sector}
                <span className="text-slate-400">{sector.direction === "up" ? "↑" : sector.direction === "down" ? "↓" : "→"}</span>
              </span>
            ))}
          </div>
        </div>
      </div>
    </article>
  );
}
