"use client";

import { useState } from "react";
import { Sidebar } from "@/components/ui/sidebar";
import { Topbar } from "@/components/ui/topbar";
import { Breadcrumbs } from "@/components/ui/breadcrumb";
import { CommandPalette } from "@/components/ui/command-palette";
import { MobileNav } from "@/components/ui/mobile-nav";
import { Menu, Terminal } from "lucide-react";
import { useRouter, usePathname } from "next/navigation";
import { useEffect, useCallback } from "react";
import FinsightChat from "@/components/finsight";
import { useUser } from "@clerk/nextjs";
import { cn } from "@/lib/utils";

const APP_ROUTES = ["/dashboard", "/predictor", "/news", "/screener", "/portfolio"];

export function AppLayout({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [finsightOpen, setFinsightOpen] = useState(false);
  const router = useRouter();
  const pathname = usePathname();
  const { user } = useUser();

  const handleArrowNav = useCallback((e: KeyboardEvent) => {
    // Only trigger if no input/textarea is focused
    if (document.activeElement?.tagName === "INPUT" || document.activeElement?.tagName === "TEXTAREA") {
      return;
    }

    if (e.ctrlKey || e.metaKey) return;

    const currentIndex = APP_ROUTES.indexOf(pathname);
    if (currentIndex === -1) return;

    if (e.key === "ArrowRight" || (e.key === "ArrowDown" && e.altKey)) {
      const nextIndex = (currentIndex + 1) % APP_ROUTES.length;
      router.push(APP_ROUTES[nextIndex]);
    } else if (e.key === "ArrowLeft" || (e.key === "ArrowUp" && e.altKey)) {
      const prevIndex = (currentIndex - 1 + APP_ROUTES.length) % APP_ROUTES.length;
      router.push(APP_ROUTES[prevIndex]);
    }
  }, [pathname, router]);

  useEffect(() => {
    window.addEventListener("keydown", handleArrowNav);
    return () => window.removeEventListener("keydown", handleArrowNav);
  }, [handleArrowNav]);

  return (
    <div className="min-h-screen bg-background">
      <CommandPalette />
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar - Fixed position */}
      <div
        className={`
          fixed inset-y-0 left-0 z-50 w-[240px] transition-transform duration-300 ease-in-out
          ${sidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}
        `}
      >
        <Sidebar 
          onClose={() => setSidebarOpen(false)} 
          onOpenFinsight={() => setFinsightOpen(true)}
        />
      </div>

      {/* Main content wrapper - with left padding to account for sidebar */}
      <div className="lg:pl-[240px] flex flex-col min-h-screen">
        {/* Mobile hamburger header */}
        <div className="flex items-center bg-card/80 backdrop-blur-xl border-b border-border/50 lg:hidden px-4 h-[60px] sticky top-0 z-30">
          <button
            onClick={() => setSidebarOpen(true)}
            className="w-9 h-9 flex items-center justify-center rounded-xl text-muted-foreground hover:bg-accent mr-3"
          >
            <Menu className="h-5 w-5" />
          </button>
          <span className="font-bold text-[15px] text-foreground tracking-tight">Finsight AI</span>
        </div>

        {/* Desktop topbar */}
        <div className="hidden lg:block sticky top-0 z-20">
          <Topbar />
        </div>

        {/* Page content */}
        <main className={cn(
          "w-full mx-auto flex flex-col",
          pathname === '/finsight' 
            ? "p-0 max-w-none h-[calc(100vh-60px)] overflow-hidden" 
            : "p-4 md:p-6 lg:p-8 max-w-[1600px] flex-1 pb-[80px] lg:pb-8"
        )}>
          {pathname !== '/finsight' && pathname !== '/markets' && <Breadcrumbs />}
          <div className={cn(
            "animate-fade-in-up flex flex-col",
            pathname === '/finsight' ? "h-full w-full" : "flex-1"
          )}>
            {children}
          </div>
        </main>

        {/* Bottom Navigation for Mobile */}
        <div className="lg:hidden fixed bottom-0 left-0 right-0 z-30 bg-card/80 backdrop-blur-xl border-t border-border/50 px-4 py-2 shadow-[0_-4px_12px_rgba(0,0,0,0.05)]">
          <MobileNav />
        </div>

        {/* Floating Finsight AI Button - Hide on /finsight page */}
        {pathname !== '/finsight' && (
          <button
            onClick={() => setFinsightOpen(true)}
            className="fixed bottom-20 lg:bottom-8 right-4 lg:right-8 z-40 flex items-center justify-center w-14 h-14 bg-[#00d68f] text-[#070a0d] rounded-full shadow-2xl hover:scale-105 transition-transform"
          >
            <Terminal className="w-6 h-6" />
          </button>
        )}

        {/* Finsight AI Global Drawer */}
        {finsightOpen && (
          <>
            <div 
              className="fixed inset-0 z-[90] bg-black/50 backdrop-blur-sm"
              onClick={() => setFinsightOpen(false)}
            />
            <div className="fixed inset-y-0 right-0 z-[100] w-full max-w-[400px] sm:max-w-[500px] md:max-w-2xl lg:max-w-4xl transition-transform duration-300 shadow-2xl">
              <FinsightChat 
                userId={user?.id || 'anonymous'} 
                onClose={() => setFinsightOpen(false)} 
                isOverlay={true} 
              />
            </div>
          </>
        )}
      </div>
    </div>
  );
}
