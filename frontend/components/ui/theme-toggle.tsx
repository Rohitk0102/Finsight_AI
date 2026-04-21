"use client";

import { Moon, Sun } from "lucide-react";
import { cn } from "@/lib/utils";
import { useTheme } from "@/components/providers/theme-provider";

interface ThemeToggleProps {
  className?: string;
}

export function ThemeToggle({ className }: ThemeToggleProps) {
  const { theme, mounted, toggleTheme } = useTheme();

  // Return placeholder during SSR/hydration to ensure consistent HTML
  if (!mounted) {
    return (
      <div
        className={cn("w-9 h-9 rounded-xl", className)}
        aria-hidden="true"
      />
    );
  }

  return (
    <button
      onClick={toggleTheme}
      className={cn(
        "w-9 h-9 flex items-center justify-center rounded-xl text-muted-foreground hover:bg-accent/50 hover:text-foreground transition-colors",
        className
      )}
      aria-label="Toggle theme"
      title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
    >
      {theme === "dark" ? (
        <Sun className="h-4 w-4" />
      ) : (
        <Moon className="h-4 w-4" />
      )}
    </button>
  );
}
