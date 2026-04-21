"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard, TrendingUp, Newspaper,
  SlidersHorizontal, Briefcase, Settings,
  LogOut, HelpCircle, Leaf, CandlestickChart,
} from "lucide-react";
import { useClerk, useUser } from "@clerk/nextjs";
import { toast } from "sonner";
import { useEffect, useState } from "react";
import { marketsFeatureEnabled } from "@/lib/markets/feature-flag";
import { useMarketPulseStore } from "@/lib/markets/store";

const menuItems = [
  { href: "/dashboard", label: "Dashboard",   icon: LayoutDashboard, badge: null },
  { href: "/predictor", label: "Predictor",   icon: TrendingUp,      badge: "AI" },
  { href: "/news",      label: "Market News", icon: Newspaper,        badge: null },
  { href: "/screener",  label: "Screener",    icon: SlidersHorizontal,badge: null },
  { href: "/portfolio", label: "Portfolio",   icon: Briefcase,        badge: null },
];

const generalItems = [
  { href: "/settings", label: "Settings", icon: Settings },
];

interface SidebarProps {
  onClose?: () => void;
}

export function Sidebar({ onClose }: SidebarProps) {
  const pathname = usePathname();
  const { signOut } = useClerk();
  const { user } = useUser();
  const [mounted, setMounted] = useState(false);
  const breakingNewsCount = useMarketPulseStore((state) => state.breakingNewsCount);

  const sidebarMenuItems = marketsFeatureEnabled
    ? [
        ...menuItems.slice(0, 2),
        { href: "/markets", label: "Market Pulse", icon: CandlestickChart, badge: breakingNewsCount > 0 ? String(breakingNewsCount) : null },
        ...menuItems.slice(2),
      ]
    : menuItems;

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleLogout = async () => {
    try {
      await signOut();
      toast.success("Signed out successfully");
    } catch (err: any) {
      toast.error("Failed to sign out");
    }
  };

  const isActive = (href: string) =>
    pathname === href || (href !== "/dashboard" && pathname.startsWith(href));

  if (!mounted) {
    return (
      <aside
        className="fixed left-0 top-0 bottom-0 w-[240px] flex flex-col z-50
                   bg-card/80 backdrop-blur-xl border-r border-border/50
                   shadow-2xl shadow-black/10"
      >
        <div className="px-5 py-5 flex items-center gap-3 border-b border-border/50">
          <div className="w-9 h-9 rounded-xl bg-muted animate-pulse" />
          <div className="h-4 w-24 bg-muted rounded animate-pulse" />
        </div>
      </aside>
    );
  }

  return (
    <aside
      className="fixed left-0 top-0 bottom-0 w-[240px] flex flex-col z-50
                 bg-card/80 backdrop-blur-xl border-r border-border/50
                 shadow-2xl shadow-black/10"
      style={{ fontFamily: "Inter, system-ui, sans-serif" }}
    >
      {/* Logo */}
      <div className="px-5 py-5 flex items-center gap-3 border-b border-border/50">
        <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 
                        bg-gradient-to-br from-primary to-primary/80 shadow-lg shadow-primary/20">
          <Leaf size={18} className="text-primary-foreground" />
        </div>
        <span className="font-bold text-[15px] text-foreground tracking-tight">
          Finsight AI
        </span>
      </div>

      {/* Scrollable content area */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden px-4 py-4">
        {/* MENU section */}
        <div className="mb-6">
          <p className="text-[10px] font-semibold text-muted-foreground tracking-widest uppercase px-2 mb-2">
            Menu
          </p>
          <nav className="space-y-0.5">
            {sidebarMenuItems.map(({ href, label, icon: Icon, badge }) => {
              const active = isActive(href);
              return (
                <Link
                  key={href}
                  href={href}
                  onClick={onClose}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2.5 rounded-xl text-[13.5px] font-medium transition-all duration-200",
                    active
                      ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20"
                      : "text-muted-foreground hover:text-foreground hover:bg-accent/50 hover:backdrop-blur-sm"
                  )}
                >
                  <Icon className="h-4 w-4 flex-shrink-0" />
                  <span className="flex-1">{label}</span>
                  {badge && (
                    <span
                      className={cn(
                        "text-[10px] font-bold px-1.5 py-0.5 rounded-full",
                        active
                          ? "bg-primary-foreground/20 text-primary-foreground"
                          : href === "/markets"
                          ? "bg-rose-500/[0.12] text-rose-300"
                          : "bg-primary/10 text-primary"
                      )}
                    >
                      {badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* GENERAL section */}
        <div>
          <p className="text-[10px] font-semibold text-muted-foreground tracking-widest uppercase px-2 mb-2">
            General
          </p>
          <nav className="space-y-0.5">
            {generalItems.map(({ href, label, icon: Icon }) => {
              const active = isActive(href);
              return (
                <Link
                  key={href}
                  href={href}
                  onClick={onClose}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2.5 rounded-xl text-[13.5px] font-medium transition-all duration-200",
                    active
                      ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20"
                      : "text-muted-foreground hover:text-foreground hover:bg-accent/50 hover:backdrop-blur-sm"
                  )}
                >
                  <Icon className="h-4 w-4 flex-shrink-0" />
                  {label}
                </Link>
              );
            })}

            <button
              className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-[13.5px] font-medium 
                         text-muted-foreground hover:text-foreground hover:bg-accent/50 hover:backdrop-blur-sm 
                         transition-all duration-200"
            >
              <HelpCircle className="h-4 w-4 flex-shrink-0" />
              Help
            </button>

            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-[13.5px] font-medium 
                         text-muted-foreground hover:text-destructive hover:bg-destructive/10 
                         transition-all duration-200"
            >
              <LogOut className="h-4 w-4 flex-shrink-0" />
              Logout
            </button>
          </nav>
        </div>
      </div>

      {/* Bottom gradient fade */}
      <div className="absolute bottom-0 left-0 right-0 h-20 
                      bg-gradient-to-t from-card/80 to-transparent pointer-events-none" />
    </aside>
  );
}
