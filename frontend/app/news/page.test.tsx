import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";

import NewsPage from "./page";

const marketMock = vi.fn();
const tickerMock = vi.fn();
const listMock = vi.fn();
const toastErrorMock = vi.fn();

vi.mock("@/lib/api/client", () => ({
  newsApi: {
    list: (...args: unknown[]) => listMock(...args),
    market: (...args: unknown[]) => marketMock(...args),
    ticker: (...args: unknown[]) => tickerMock(...args),
  },
}));

vi.mock("sonner", () => ({
  toast: {
    error: (...args: unknown[]) => toastErrorMock(...args),
  },
}));

vi.mock("next/image", () => ({
  default: (props: any) => <img {...props} alt={props.alt ?? ""} />,
}));

describe("NewsPage", () => {
  beforeEach(() => {
    listMock.mockReset();
    marketMock.mockReset();
    tickerMock.mockReset();
    toastErrorMock.mockReset();
  });

  it("renders description-first payload without triggering error toast", async () => {
    listMock.mockResolvedValue({
      data: {
        articles: [
          {
            id: "1",
            ticker: null,
            title: "Markets rally on earnings optimism",
            description: "Description only payload from backend.",
            url: "https://example.com/news-1",
            source: "Example Source",
            published_at: "2026-04-18T10:00:00Z",
            sentiment: "positive",
            sentiment_score: 0.6,
            category: "general",
            image_url: null,
          },
        ],
        total: 1,
        page: 1,
        limit: 30,
        has_more: false,
      },
    });

    render(<NewsPage />);

    await waitFor(() => {
      expect(screen.getByText("Markets rally on earnings optimism")).toBeInTheDocument();
    });
    expect(screen.getByText("Description only payload from backend.")).toBeInTheDocument();
    expect(toastErrorMock).not.toHaveBeenCalled();
  });

  it("falls back to summary when description is missing", async () => {
    listMock.mockResolvedValue({
      data: {
        articles: [
          {
            id: "2",
            ticker: null,
            title: "Legacy payload article",
            summary: "Legacy summary field still renders.",
            url: "https://example.com/news-2",
            source: "Legacy Source",
            published_at: "2026-04-18T10:00:00Z",
            sentiment: "neutral",
            sentiment_score: 0.0,
            category: "general",
            image_url: null,
          },
        ],
        total: 1,
        page: 1,
        limit: 30,
        has_more: false,
      },
    });

    render(<NewsPage />);

    await waitFor(() => {
      expect(screen.getByText("Legacy payload article")).toBeInTheDocument();
    });
    expect(screen.getByText("Legacy summary field still renders.")).toBeInTheDocument();
    expect(toastErrorMock).not.toHaveBeenCalled();
  });

  it("loads unfiltered by default and shows a service error instead of the empty state on 503", async () => {
    listMock.mockRejectedValue({
      response: {
        status: 503,
      },
    });

    render(<NewsPage />);

    await waitFor(() => {
      expect(listMock).toHaveBeenCalledWith({ page: 1, limit: 30 });
    });
    await waitFor(() => {
      expect(screen.getByText("News service unavailable")).toBeInTheDocument();
    });

    expect(screen.queryByText("No news found")).not.toBeInTheDocument();
    expect(toastErrorMock).toHaveBeenCalledWith(
      "News providers are temporarily unavailable. Please try again in a few minutes."
    );
  });
});
