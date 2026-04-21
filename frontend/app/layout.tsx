import type { Metadata } from "next";
import { ClerkProvider } from "@clerk/nextjs";
import "./globals.css";
import { Toaster } from "sonner";
import { ThemeProvider } from "@/components/providers/theme-provider";

export const metadata: Metadata = {
  title: "Finsight AI — Smart Stock Predictions",
  description: "AI-powered stock market predictions, news analysis, and portfolio management",
  icons: { icon: "/favicon.ico" },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <ClerkProvider>
      <html lang="en" suppressHydrationWarning>
        <head>
          <script
            dangerouslySetInnerHTML={{
              __html: `
                (function () {
                  try {
                    var stored = localStorage.getItem('theme');
                    var theme = stored === 'light' || stored === 'dark' ? stored : 'dark';
                    var root = document.documentElement;
                    root.classList.toggle('dark', theme === 'dark');
                    root.setAttribute('data-theme', theme);
                  } catch (e) {}
                })();
              `,
            }}
          />
        </head>
        <body className="antialiased">
          <ThemeProvider>
            {children}
            <Toaster richColors position="top-right" />
          </ThemeProvider>
        </body>
      </html>
    </ClerkProvider>
  );
}
