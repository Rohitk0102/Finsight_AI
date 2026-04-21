"use client";

import { useState } from "react";
import { Sidebar } from "@/components/ui/sidebar";
import { Topbar } from "@/components/ui/topbar";
import { Menu } from "lucide-react";

export function AppLayout({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-background">
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
        <Sidebar onClose={() => setSidebarOpen(false)} />
      </div>

      {/* Main content wrapper - with left padding to account for sidebar */}
      <div className="lg:pl-[240px]">
        {/* Mobile hamburger header */}
        <div className="flex items-center bg-card/80 backdrop-blur-xl border-b border-border/50 lg:hidden px-4 h-[60px] sticky top-0 z-30">
          <button
            onClick={() => setSidebarOpen(true)}
            className="w-9 h-9 flex items-center justify-center rounded-xl text-muted-foreground hover:bg-accent mr-3"
          >
            <Menu className="h-5 w-5" />
          </button>
          <span className="font-bold text-[15px] text-foreground">Finsight AI</span>
        </div>

        {/* Desktop topbar */}
        <div className="hidden lg:block sticky top-0 z-20">
          <Topbar />
        </div>

        {/* Page content */}
        <main className="p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
