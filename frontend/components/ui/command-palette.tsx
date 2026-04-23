"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Search, TrendingUp, Newspaper, Briefcase, LayoutDashboard, SlidersHorizontal, X } from "lucide-react";

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const router = useRouter();

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      setOpen((o) => !o);
    }
  }, []);

  useEffect(() => {
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  if (!open) return null;

  const actions = [
    { icon: LayoutDashboard, label: "Go to Dashboard", href: "/dashboard" },
    { icon: TrendingUp,      label: "Stock Predictor", href: "/predictor" },
    { icon: Newspaper,       label: "Market News",     href: "/news" },
    { icon: SlidersHorizontal, label: "Stock Screener",  href: "/screener" },
    { icon: Briefcase,       label: "Portfolio",       href: "/portfolio" },
  ];

  return (
    <div className="fixed inset-0 z-[100] flex items-start justify-center pt-[15vh] p-4 bg-background/40 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-xl bg-card rounded-2xl shadow-2xl border border-border/50 overflow-hidden animate-slide-in-up">
        <div className="flex items-center px-4 py-3 border-b border-border/50">
          <Search className="h-5 w-5 text-muted-foreground mr-3" />
          <input 
            autoFocus
            placeholder="Type a command or search..."
            className="flex-1 bg-transparent border-none outline-none text-[15px] placeholder:text-muted-foreground"
          />
          <button onClick={() => setOpen(false)} className="p-1 hover:bg-accent rounded-md transition-colors">
            <X className="h-4 w-4 text-muted-foreground" />
          </button>
        </div>
        
        <div className="p-2">
          <p className="px-3 py-2 text-[11px] font-bold text-muted-foreground uppercase tracking-widest">Quick Navigation</p>
          <div className="space-y-1">
            {actions.map((action) => (
              <button
                key={action.href}
                onClick={() => {
                  router.push(action.href);
                  setOpen(false);
                }}
                className="w-full flex items-center gap-3 px-3 py-3 rounded-xl hover:bg-accent transition-colors text-left group"
              >
                <action.icon className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
                <span className="text-[14px] font-medium">{action.label}</span>
                <span className="ml-auto text-[11px] text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity">Go to</span>
              </button>
            ))}
          </div>
        </div>
        
        <div className="px-4 py-3 bg-muted/30 border-t border-border/50 flex items-center justify-between">
          <p className="text-[11px] text-muted-foreground">Tip: Press <kbd className="font-sans px-1 bg-muted rounded border border-border/50">Esc</kbd> to close</p>
          <div className="flex items-center gap-3 text-[11px] text-muted-foreground">
            <span className="flex items-center gap-1"><kbd className="px-1 bg-muted rounded border border-border/50">↑↓</kbd> Navigate</span>
            <span className="flex items-center gap-1"><kbd className="px-1 bg-muted rounded border border-border/50">Enter</kbd> Select</span>
          </div>
        </div>
      </div>
    </div>
  );
}
