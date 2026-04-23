"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  LayoutDashboard, TrendingUp, Newspaper, 
  Briefcase, CandlestickChart, SlidersHorizontal 
} from "lucide-react";
import { cn } from "@/lib/utils";
import { marketsFeatureEnabled } from "@/lib/markets/feature-flag";

export function MobileNav() {
  const pathname = usePathname();

  const navItems = [
    { href: "/dashboard", label: "Home", icon: LayoutDashboard },
    { href: "/predictor", label: "Predict", icon: TrendingUp },
    ...(marketsFeatureEnabled 
      ? [{ href: "/markets", label: "Pulse", icon: CandlestickChart }]
      : []
    ),
    { href: "/portfolio", label: "Assets", icon: Briefcase },
    { href: "/news", label: "News", icon: Newspaper },
  ];

  return (
    <nav className="flex items-center justify-around w-full">
      {navItems.map(({ href, label, icon: Icon }) => {
        const isActive = pathname === href || (href !== "/dashboard" && pathname.startsWith(href));
        return (
          <Link
            key={href}
            href={href}
            className={cn(
              "flex flex-col items-center gap-1 px-2 py-1 transition-colors duration-200",
              isActive ? "text-primary" : "text-muted-foreground"
            )}
          >
            <Icon className={cn("h-5 w-5", isActive && "animate-pulse-ring")} />
            <span className="text-[10px] font-medium tracking-tight">{label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
