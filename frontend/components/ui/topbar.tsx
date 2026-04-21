"use client";

import { Search, Bell, Mail } from "lucide-react";
import { useUser, useClerk } from "@clerk/nextjs";
import { useEffect, useState } from "react";
import { ThemeToggle } from "@/components/ui/theme-toggle";

interface TopbarProps {
  pageTitle?: string;
  pageSubtitle?: string;
}

export function Topbar({ pageTitle, pageSubtitle }: TopbarProps) {
  const { user, isLoaded } = useUser();
  const { signOut } = useClerk();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const name = user?.fullName ?? user?.primaryEmailAddress?.emailAddress?.split("@")[0] ?? "User";
  const email = user?.primaryEmailAddress?.emailAddress ?? "";
  const initials = name
    .split(" ")
    .map((w) => w[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  return (
    <header className="h-[60px] flex items-center gap-4 px-6 
                       bg-card/80 backdrop-blur-xl border-b border-border/50
                       shadow-sm">
      {/* Search */}
      <div className="flex-1 max-w-sm relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <input
          type="text"
          placeholder="Search stocks, news..."
          className="w-full pl-10 pr-12 py-2 text-[13px] 
                     bg-muted/50 backdrop-blur-sm border border-border/50 rounded-xl 
                     text-foreground placeholder:text-muted-foreground 
                     focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/10 
                     transition-all"
        />
        <kbd className="absolute right-3 top-1/2 -translate-y-1/2 
                        hidden sm:inline-flex items-center gap-0.5 px-1.5 py-0.5 
                        text-[10px] font-medium text-muted-foreground 
                        bg-muted/50 backdrop-blur-sm rounded border border-border/50">
          ⌘F
        </kbd>
      </div>

      <div className="flex items-center gap-2 ml-auto">
        {/* Mail */}
        <button className="w-9 h-9 flex items-center justify-center rounded-xl 
                           text-muted-foreground hover:bg-accent/50 hover:text-foreground 
                           hover:backdrop-blur-sm transition-all duration-200">
          <Mail size={18} />
        </button>

        {/* Bell with notification dot */}
        <button className="relative w-9 h-9 flex items-center justify-center rounded-xl 
                           text-muted-foreground hover:bg-accent/50 hover:text-foreground 
                           hover:backdrop-blur-sm transition-all duration-200">
          <Bell size={18} />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-destructive rounded-full 
                           border-2 border-card shadow-lg shadow-destructive/20" />
        </button>

        {/* Theme toggle */}
        <ThemeToggle />

        {/* Divider */}
        <div className="w-px h-6 bg-border/50 mx-1" />

        {/* User avatar - only render when mounted and loaded */}
        {mounted && isLoaded && user ? (
          <button
            onClick={() => signOut({ redirectUrl: "/sign-in" })}
            className="flex items-center gap-2.5 group hover:bg-accent/50 rounded-xl px-2 py-1.5 
                       transition-all duration-200"
            title="Sign out"
          >
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-primary/80 
                            flex items-center justify-center flex-shrink-0 
                            shadow-lg shadow-primary/20">
              <span className="text-[11px] font-bold text-primary-foreground">{initials}</span>
            </div>
            <div className="hidden sm:block leading-tight">
              <p className="text-[13px] font-semibold text-foreground leading-none">{name}</p>
              <p className="text-[11px] text-muted-foreground mt-0.5 leading-none">{email}</p>
            </div>
          </button>
        ) : (
          <div className="w-8 h-8 rounded-full bg-muted animate-pulse" />
        )}
      </div>
    </header>
  );
}
