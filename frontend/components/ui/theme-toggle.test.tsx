import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { render, waitFor, fireEvent, cleanup } from "@testing-library/react";
import { renderToString } from "react-dom/server";
import { ThemeProvider } from "@/components/providers/theme-provider";
import { ThemeToggle } from "./theme-toggle";

function renderWithProvider() {
  return render(
    <ThemeProvider>
      <ThemeToggle />
    </ThemeProvider>
  );
}

describe("ThemeToggle", () => {
  let store: Map<string, string>;

  beforeEach(() => {
    store = new Map<string, string>();

    const localStorageMock: Storage = {
      getItem: (key: string) => store.get(key) ?? null,
      setItem: (key: string, value: string) => {
        store.set(key, value);
      },
      removeItem: (key: string) => {
        store.delete(key);
      },
      clear: () => {
        store.clear();
      },
      key: (index: number) => Array.from(store.keys())[index] ?? null,
      get length() {
        return store.size;
      },
    };

    Object.defineProperty(window, "localStorage", {
      value: localStorageMock,
      configurable: true,
      writable: true,
    });

    document.documentElement.className = "";
    document.documentElement.removeAttribute("data-theme");
  });

  afterEach(() => {
    cleanup();
  });

  it("renders non-interactive placeholder markup on server", () => {
    const serverHTML = renderToString(
      <ThemeProvider>
        <ThemeToggle />
      </ThemeProvider>
    );

    expect(serverHTML).toContain("w-9 h-9");
    expect(serverHTML).not.toContain("<button");
  });

  it("hydrates from saved light theme without crashing", async () => {
    store.set("theme", "light");
    const { container } = renderWithProvider();

    await waitFor(() => {
      const button = container.querySelector("button");
      expect(button).toBeTruthy();
    });

    expect(document.documentElement.classList.contains("dark")).toBe(false);
    expect(document.documentElement.getAttribute("data-theme")).toBe("light");
  });

  it("hydrates from invalid saved value by falling back to dark", async () => {
    store.set("theme", "invalid");
    const { container } = renderWithProvider();

    await waitFor(() => {
      const button = container.querySelector("button");
      expect(button).toBeTruthy();
    });

    expect(document.documentElement.classList.contains("dark")).toBe(true);
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
  });

  it("toggles and persists theme on click", async () => {
    store.set("theme", "dark");
    const { container } = renderWithProvider();

    await waitFor(() => {
      const button = container.querySelector("button");
      expect(button).toBeTruthy();
    });

    const button = container.querySelector("button");
    if (!button) throw new Error("Theme toggle button was not rendered");

    fireEvent.click(button);
    await waitFor(() => {
      expect(store.get("theme")).toBe("light");
      expect(document.documentElement.classList.contains("dark")).toBe(false);
      expect(document.documentElement.getAttribute("data-theme")).toBe("light");
    });

    fireEvent.click(button);
    await waitFor(() => {
      expect(store.get("theme")).toBe("dark");
      expect(document.documentElement.classList.contains("dark")).toBe(true);
      expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
    });
  });
});
