import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./app/**/*.{ts,tsx}",
    "./src/**/*.{ts,tsx}",
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: { "2xl": "1400px" },
    },
    extend: {
      colors: {
        border:     "hsl(var(--border))",
        input:      "hsl(var(--input))",
        ring:       "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT:    "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT:    "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT:    "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT:    "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT:    "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        card: {
          DEFAULT:    "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        // Semantic finance colors
        positive: "#22C55E",
        negative: "#EF4444",
        neutral:  "#f59e0b",
        bull:     "#22C55E",
        bear:     "#EF4444",
        // Chart palette (matches reference)
        "chart-1": "#005e30",
        "chart-2": "#008b46",
        "chart-3": "#49a46e",
        "chart-4": "#85bd98",
        "chart-5": "#bad6c3",
      },
      borderRadius: {
        lg:   "var(--radius)",
        md:   "calc(var(--radius) - 2px)",
        sm:   "calc(var(--radius) - 4px)",
        card: "1rem",
        "2xl": "1rem",
      },
      fontSize: {
        "page-title": ["22px", { fontWeight: "600", lineHeight: "1.3", letterSpacing: "-0.02em" }],
        "card-title":  ["15px", { fontWeight: "500", lineHeight: "1.4" }],
        "body-sm":     ["13px", { fontWeight: "400", lineHeight: "1.5" }],
        "label-xs":    ["11px", { fontWeight: "400", lineHeight: "1.4" }],
      },
      spacing: {
        kpi: "44px",
        sidebar: "16rem",  /* 256px */
      },
      keyframes: {
        "accordion-down": { from: { height: "0" }, to: { height: "var(--radix-accordion-content-height)" } },
        "accordion-up":   { from: { height: "var(--radix-accordion-content-height)" }, to: { height: "0" } },
        "slide-in-up": {
          from: { opacity: "0", transform: "translateY(16px)" },
          to:   { opacity: "1", transform: "translateY(0)" },
        },
        "fade-in": {
          from: { opacity: "0", transform: "translateY(-6px)" },
          to:   { opacity: "1", transform: "translateY(0)" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%":      { transform: "translateY(-6px)" },
        },
        shimmer: {
          "0%":   { transform: "translateX(-100%)" },
          "100%": { transform: "translateX(100%)" },
        },
        "pulse-green": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.5", color: "#22c55e" },
        },
      },
      animation: {
        "accordion-down":  "accordion-down 0.2s ease-out",
        "accordion-up":    "accordion-up 0.2s ease-out",
        "slide-in-up":     "slide-in-up 0.4s cubic-bezier(0,0,0.2,1) both",
        "fade-in":         "fade-in 0.3s cubic-bezier(0,0,0.2,1) both",
        float:             "float 3s ease-in-out infinite",
        shimmer:           "shimmer 1.5s infinite",
        "pulse-green":     "pulse-green 2s ease-in-out infinite",
      },
      transitionDuration: {
        DEFAULT: "200ms",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
