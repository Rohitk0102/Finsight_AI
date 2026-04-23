"use client";

import { ChevronLeft, ChevronRight, MoreHorizontal } from "lucide-react";
import { cn } from "@/lib/utils";

interface PaginationProps {
  currentPage: number;
  totalCount: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  className?: string;
}

export function Pagination({
  currentPage,
  totalCount,
  pageSize,
  onPageChange,
  className,
}: PaginationProps) {
  const totalPages = Math.ceil(totalCount / pageSize);

  if (totalPages <= 1) return null;

  const getPageNumbers = () => {
    const pages = [];
    const showMax = 5;

    if (totalPages <= showMax) {
      for (let i = 1; i <= totalPages; i++) pages.push(i);
    } else {
      pages.push(1);
      if (currentPage > 3) pages.push("ellipsis");

      const start = Math.max(2, currentPage - 1);
      const end = Math.min(totalPages - 1, currentPage + 1);

      for (let i = start; i <= end; i++) {
        if (!pages.includes(i)) pages.push(i);
      }

      if (currentPage < totalPages - 2) pages.push("ellipsis");
      if (!pages.includes(totalPages)) pages.push(totalPages);
    }
    return pages;
  };

  return (
    <nav className={cn("flex items-center justify-center gap-2 py-8 animate-fade-in", className)}>
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className="h-10 w-10 flex items-center justify-center rounded-xl border border-border hover:bg-accent disabled:opacity-30 disabled:hover:bg-transparent transition-all"
        aria-label="Previous Page"
      >
        <ChevronLeft className="h-5 w-5" />
      </button>

      <div className="flex items-center gap-1.5">
        {getPageNumbers().map((page, i) => (
          page === "ellipsis" ? (
            <div key={`ellipsis-${i}`} className="w-10 h-10 flex items-center justify-center text-muted-foreground">
              <MoreHorizontal className="h-4 w-4" />
            </div>
          ) : (
            <button
              key={page}
              onClick={() => onPageChange(page as number)}
              className={cn(
                "h-10 w-10 flex items-center justify-center rounded-xl font-bold text-[13px] transition-all",
                currentPage === page
                  ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20 scale-110"
                  : "border border-border hover:bg-accent text-muted-foreground hover:text-foreground"
              )}
            >
              {page}
            </button>
          )
        ))}
      </div>

      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="h-10 w-10 flex items-center justify-center rounded-xl border border-border hover:bg-accent disabled:opacity-30 disabled:hover:bg-transparent transition-all"
        aria-label="Next Page"
      >
        <ChevronRight className="h-5 w-5" />
      </button>
    </nav>
  );
}
