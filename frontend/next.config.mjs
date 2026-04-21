import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const isDev = process.env.NODE_ENV !== "production";

// In dev the backend runs on plain HTTP (see run.sh / restart_backend.sh),
// so the Next.js rewrite proxy doesn't hit self-signed TLS at all. This flag
// stays as defense-in-depth for any other outbound HTTPS calls during dev.
if (isDev) {
  process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0";
}

const csp = [
  "default-src 'self'",
  `script-src 'self' 'unsafe-inline' ${isDev ? "'unsafe-eval' " : ""}https://challenges.cloudflare.com https://*.clerk.accounts.dev https://*.clerk.com`,
  "style-src 'self' 'unsafe-inline' https:",
  "img-src 'self' data: blob: https:",
  "font-src 'self' data: https:",
  "connect-src 'self' https: wss: ws: http://localhost:* https://localhost:* https://127.0.0.1:*",
  "frame-src 'self' https://challenges.cloudflare.com https://*.clerk.accounts.dev https://*.clerk.com",
  "worker-src 'self' blob:",
  "object-src 'none'",
  "base-uri 'self'",
  "frame-ancestors 'self'",
].join("; ");

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  turbopack: {
    root: __dirname,
  },
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "**.finnhub.io" },
      { protocol: "https", hostname: "**.newsapi.org" },
      { protocol: "https", hostname: "static.finnhub.io" },
    ],
  },
  async rewrites() {
    // Backend rewrite runs server-side (undici). Must use plain HTTP — undici
    // does NOT honour NODE_TLS_REJECT_UNAUTHORIZED, so an https:// destination
    // with a self-signed cert causes UNABLE_TO_VERIFY_LEAF_SIGNATURE.
    // Force http:// so env-var pollution (e.g. sourcing backend/.env in run.sh)
    // can never accidentally send TLS traffic to a plain-HTTP uvicorn process.
    const rawBase =
      process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
    const backendBase = rawBase.replace(/^https:\/\//, "http://");
    return [
      {
        source: "/api/backend/:path*",
        destination: `${backendBase}/:path*`,
      },
    ];
  },
  // Configure webpack to handle Node.js modules in client-side code
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
      };
    }
    return config;
  },
  // Allow self-signed certificates in development
  experimental: {
    serverActions: {
      bodySizeLimit: '2mb',
    },
  },
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          {
            key: "Content-Security-Policy",
            value: csp,
          },
        ],
      },
    ];
  },
};

export default nextConfig;
