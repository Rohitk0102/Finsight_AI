import Link from "next/link";
import {
  TrendingUp, BarChart2, Newspaper, Briefcase,
  ArrowRight, Leaf, Sparkles, Activity,
  Shield, Zap,
} from "lucide-react";
import { ThemeToggle } from "@/components/ui/theme-toggle";

/* ── static data ─────────────────────────────────────────────── */
const features = [
  {
    icon: TrendingUp,
    tag: "Core",
    title: "AI Stock Predictor",
    desc: "Ensemble ML — LSTM + XGBoost + Prophet — delivering 1d / 7d / 30d price targets with calibrated confidence scores.",
  },
  {
    icon: Newspaper,
    tag: "Intelligence",
    title: "News Sentiment",
    desc: "Real-time market news scored with FinBERT sentiment — know the mood before it moves the market.",
  },
  {
    icon: BarChart2,
    tag: "Analytics",
    title: "Technical Analysis",
    desc: "RSI, MACD, Bollinger Bands and 17 more indicators computed live on OHLCV data from NSE / BSE.",
  },
  {
    icon: Briefcase,
    tag: "Brokers",
    title: "Portfolio Hub",
    desc: "Connect Zerodha, Upstox, Angel One & Groww. Unified P&L, holdings, and AI-driven recommendations.",
  },
];

const stats = [
  { value: "3",   label: "ML Models",  note: "LSTM · XGBoost · Prophet" },
  { value: "20+", label: "Indicators", note: "Technical signals" },
  { value: "30d", label: "Horizon",    note: "Max prediction window" },
  { value: "4",   label: "Brokers",    note: "Indian & global" },
];

const steps = [
  { n: "01", title: "Connect your broker",  desc: "Link Zerodha, Upstox, or Angel One in one click via OAuth." },
  { n: "02", title: "Search any stock",     desc: "Enter a ticker — NSE, BSE, NASDAQ, or indices." },
  { n: "03", title: "Get AI predictions",   desc: "Receive ensemble price targets with risk scoring instantly." },
];

const miniChart = [38, 52, 46, 60, 55, 68, 63, 78, 70, 85, 80, 94];

const liveCards = [
  { symbol: "RELIANCE", price: "₹2,847", chg: "+1.82%", up: true },
  { symbol: "HDFCBANK",  price: "₹1,612", chg: "+0.94%", up: true },
];

/* ── page ────────────────────────────────────────────────────── */
export default function HomePage() {
  return (
    <div className="min-h-screen bg-[#030a05] text-[#edf7f0] overflow-x-hidden">

      {/* ════════════════ NAV ════════════════ */}
      <nav className="fixed top-0 inset-x-0 z-50 flex items-center justify-between
                      px-6 lg:px-10 py-4
                      border-b border-white/[0.06]
                      bg-[#030a05]/80 backdrop-blur-lg">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-emerald-600/20 border border-emerald-600/30
                          flex items-center justify-center">
            <Leaf className="h-4 w-4 text-emerald-400" />
          </div>
          <span className="font-bold text-[15px] tracking-tight text-white">Finsight AI</span>
        </div>

        <div className="flex items-center gap-2">
          <Link
            href="/sign-in"
            className="hidden sm:inline-flex items-center px-4 py-2 rounded-xl
                       text-[13px] font-medium text-[#7aaa86]
                       hover:text-white hover:bg-white/5
                       transition-all duration-200"
          >
            Sign In
          </Link>
          <ThemeToggle />
          <Link
            href="/sign-up"
            className="inline-flex items-center gap-1.5 px-5 py-2 rounded-xl
                       bg-emerald-600 hover:bg-emerald-500
                       text-white text-[13px] font-semibold
                       shadow-lg shadow-emerald-950
                       transition-all duration-200 hover:-translate-y-px"
          >
            Get Started <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </nav>

      {/* ════════════════ HERO ════════════════ */}
      <section className="relative min-h-screen flex items-center pt-24 pb-20 px-6 lg:px-10 overflow-hidden">

        {/* background glows */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2
                          w-[900px] h-[600px] rounded-full
                          bg-emerald-950/60 blur-[140px]" />
          <div className="absolute top-1/2 right-0
                          w-[400px] h-[500px] rounded-full
                          bg-emerald-900/20 blur-[100px]" />
        </div>

        {/* subtle dot grid */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            backgroundImage: "radial-gradient(circle, #1a3d22 1px, transparent 1px)",
            backgroundSize: "40px 40px",
            opacity: 0.25,
          }}
        />

        <div className="max-w-7xl mx-auto w-full grid lg:grid-cols-2 gap-12 lg:gap-20 items-center relative z-10">

          {/* ── LEFT: copy ── */}
          <div>
            {/* pill badge */}
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full
                            bg-emerald-950 border border-emerald-800/60
                            text-emerald-400 text-[11px] font-bold tracking-widest uppercase
                            mb-8">
              <Sparkles className="h-3 w-3" />
              AI-Powered for Indian Markets
            </div>

            <h1 className="text-[52px] lg:text-[76px] font-black leading-[0.92] tracking-tight
                           text-white mb-6">
              Predict<br />
              Smarter,{" "}
              <span className="text-transparent bg-clip-text
                               bg-gradient-to-r from-emerald-400 via-green-300 to-teal-400">
                Invest Better
              </span>
            </h1>

            <p className="text-[16px] text-[#6d9877] leading-relaxed max-w-md mb-10">
              Finsight AI runs LSTM, XGBoost, and Prophet in an ensemble to predict
              Indian stock prices — with real-time FinBERT sentiment scoring and
              full broker integration.
            </p>

            <div className="flex flex-wrap gap-3 mb-14">
              <Link
                href="/sign-up"
                className="inline-flex items-center gap-2 px-8 py-3.5 rounded-xl
                           bg-emerald-600 hover:bg-emerald-500
                           text-white font-bold text-[15px]
                           shadow-xl shadow-emerald-950
                           transition-all duration-200 hover:-translate-y-0.5"
              >
                Start Free <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                href="/sign-in"
                className="inline-flex items-center gap-2 px-8 py-3.5 rounded-xl
                           border border-[#1e3a24] hover:border-emerald-700/50
                           text-[#7aaa86] hover:text-white font-medium text-[15px]
                           transition-all duration-200 hover:bg-emerald-950/50"
              >
                Sign In
              </Link>
            </div>

            {/* stats strip */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 pt-8 border-t border-[#172d1e]">
              {stats.map(({ value, label, note }) => (
                <div key={label}>
                  <div className="text-[30px] font-black text-emerald-400 leading-none mb-1">{value}</div>
                  <div className="text-[13px] font-semibold text-white mb-0.5">{label}</div>
                  <div className="text-[11px] text-[#4a6c54]">{note}</div>
                </div>
              ))}
            </div>
          </div>

          {/* ── RIGHT: decorative AI card ── */}
          <div className="hidden lg:flex flex-col gap-3">

            {/* main prediction card */}
            <div className="bg-[#090f0b] border border-[#1a3320] rounded-2xl p-6 shadow-2xl shadow-black/60">
              <div className="flex items-start justify-between mb-5">
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-emerald-600 mb-1">
                    AI Prediction · Live
                  </p>
                  <h3 className="text-[22px] font-black text-white tracking-tight">RELIANCE.NS</h3>
                  <p className="text-[13px] text-[#4a6c54] mt-0.5">₹2,847 · NSE</p>
                </div>
                <span className="px-3 py-1.5 rounded-full bg-emerald-500/15 border border-emerald-500/25
                                 text-emerald-400 text-[12px] font-black tracking-wide">
                  BUY
                </span>
              </div>

              {/* mini bar chart */}
              <div className="flex items-end gap-1 h-16 mb-5">
                {miniChart.map((h, i) => (
                  <div
                    key={i}
                    className={`flex-1 rounded-t-sm transition-all ${
                      i >= miniChart.length - 4 ? "bg-emerald-500" : "bg-[#1a3320]"
                    }`}
                    style={{ height: `${h}%` }}
                  />
                ))}
              </div>

              {/* price targets */}
              <div className="grid grid-cols-3 gap-2 mb-5">
                {[
                  { label: "1D Target", val: "₹2,903", pct: "+1.9%" },
                  { label: "7D Target", val: "₹2,961", pct: "+4.0%" },
                  { label: "30D Target", val: "₹3,102", pct: "+8.9%" },
                ].map(({ label, val, pct }) => (
                  <div key={label} className="bg-[#0f1f14] rounded-xl p-3 text-center">
                    <p className="text-[9px] text-[#4a6c54] uppercase tracking-wide mb-1.5">{label}</p>
                    <p className="text-[14px] font-black text-white leading-none mb-1">{val}</p>
                    <p className="text-[11px] text-emerald-400 font-bold">{pct}</p>
                  </div>
                ))}
              </div>

              {/* confidence bar */}
              <div className="flex items-center gap-3 text-[12px]">
                <span className="text-[#4a6c54] flex-shrink-0">Confidence</span>
                <div className="flex-1 h-1.5 bg-[#0f1f14] rounded-full overflow-hidden">
                  <div className="w-[87%] h-full rounded-full bg-gradient-to-r from-emerald-700 to-emerald-400" />
                </div>
                <span className="font-black text-emerald-400 flex-shrink-0">87%</span>
              </div>
            </div>

            {/* live ticker row */}
            <div className="grid grid-cols-2 gap-3">
              {liveCards.map((t) => (
                <div key={t.symbol}
                  className="bg-[#090f0b] border border-[#1a3320] rounded-xl p-4
                             hover:border-emerald-700/40 transition-colors duration-200">
                  <p className="text-[9px] font-bold uppercase tracking-widest text-[#4a6c54] mb-1.5">{t.symbol}</p>
                  <p className="text-[17px] font-black text-white leading-none mb-1">{t.price}</p>
                  <p className={`text-[12px] font-bold ${t.up ? "text-emerald-400" : "text-red-400"}`}>{t.chg}</p>
                </div>
              ))}
            </div>

            {/* sentiment strip */}
            <div className="bg-[#090f0b] border border-[#1a3320] rounded-xl p-4
                            flex items-center gap-4">
              <div className="w-9 h-9 rounded-full bg-emerald-500/15 border border-emerald-500/20
                              flex items-center justify-center flex-shrink-0">
                <Activity className="h-4 w-4 text-emerald-400" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-[12px] font-bold text-white mb-0.5">Market Sentiment</p>
                <p className="text-[11px] text-[#4a6c54] truncate">NIFTY 50 · Broadly positive</p>
              </div>
              <span className="flex-shrink-0 px-2.5 py-1 rounded-lg
                               bg-emerald-500/10 border border-emerald-500/20
                               text-emerald-400 text-[11px] font-black">
                +0.72
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* ════════════════ FEATURES ════════════════ */}
      <section className="py-28 px-6 lg:px-10 border-t border-white/[0.04]">
        <div className="max-w-7xl mx-auto">

          <div className="text-center mb-16">
            <p className="text-[11px] font-black uppercase tracking-[0.22em] text-emerald-600 mb-4">Platform</p>
            <h2 className="text-[36px] lg:text-[52px] font-black text-white tracking-tight leading-tight">
              Everything you need to<br />
              <span className="text-emerald-400">trade with confidence</span>
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {features.map(({ icon: Icon, tag, title, desc }) => (
              <div
                key={title}
                className="group relative bg-[#090f0b] border border-[#1a3320] rounded-2xl p-6
                           hover:border-emerald-700/50 hover:bg-[#0c1810]
                           transition-all duration-300 cursor-default"
              >
                {/* tag */}
                <span className="absolute top-4 right-4 text-[9px] font-black uppercase tracking-widest
                                 text-emerald-800 px-2 py-0.5 rounded-full
                                 bg-emerald-950/80 border border-emerald-900/60">
                  {tag}
                </span>

                {/* icon */}
                <div className="w-11 h-11 rounded-xl bg-emerald-500/10 border border-emerald-500/20
                                flex items-center justify-center mb-5
                                group-hover:bg-emerald-500/20 group-hover:scale-110
                                transition-all duration-300">
                  <Icon className="h-5 w-5 text-emerald-400" />
                </div>

                <h3 className="text-[15px] font-bold text-white mb-2">{title}</h3>
                <p className="text-[12px] text-[#4a6c54] leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ════════════════ HOW IT WORKS ════════════════ */}
      <section className="py-28 px-6 lg:px-10 border-t border-white/[0.04]">
        <div className="max-w-5xl mx-auto">

          <div className="text-center mb-16">
            <p className="text-[11px] font-black uppercase tracking-[0.22em] text-emerald-600 mb-4">Process</p>
            <h2 className="text-[36px] lg:text-[52px] font-black text-white tracking-tight">
              Up and running in minutes
            </h2>
          </div>

          <div className="grid md:grid-cols-3 gap-10">
            {steps.map(({ n, title, desc }, i) => (
              <div key={n} className="relative">
                {/* connector line */}
                {i < steps.length - 1 && (
                  <div className="hidden md:block absolute top-8 left-full w-full h-px
                                  bg-gradient-to-r from-[#1a3320] to-transparent
                                  -translate-x-6 z-0" />
                )}
                <div className="relative z-10">
                  <div className="text-[60px] font-black leading-none mb-5 select-none
                                  text-transparent bg-clip-text
                                  bg-gradient-to-b from-emerald-900/80 to-transparent">
                    {n}
                  </div>
                  <h3 className="text-[16px] font-bold text-white mb-2">{title}</h3>
                  <p className="text-[13px] text-[#4a6c54] leading-relaxed">{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ════════════════ SECURITY STRIP ════════════════ */}
      <section className="py-12 px-6 lg:px-10 border-t border-white/[0.04]">
        <div className="max-w-4xl mx-auto flex flex-col sm:flex-row items-center justify-center gap-8 text-center sm:text-left">
          {[
            { icon: Shield, label: "AES-256 Encrypted", sub: "Broker tokens secured with Fernet" },
            { icon: Zap,    label: "Real-time Data",     sub: "Live prices via yfinance & NSE" },
            { icon: Activity, label: "Always-on ML",    sub: "Models retrain weekly automatically" },
          ].map(({ icon: Icon, label, sub }) => (
            <div key={label} className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-emerald-950 border border-emerald-900/50
                              flex items-center justify-center flex-shrink-0">
                <Icon className="h-4 w-4 text-emerald-600" />
              </div>
              <div>
                <p className="text-[13px] font-bold text-white">{label}</p>
                <p className="text-[11px] text-[#4a6c54]">{sub}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ════════════════ CTA BANNER ════════════════ */}
      <section className="py-20 px-6 lg:px-10">
        <div className="max-w-4xl mx-auto">
          <div
            className="relative rounded-3xl overflow-hidden border border-emerald-700/25 p-14 text-center
                       bg-gradient-to-br from-[#0d2416] via-[#0a1d12] to-[#061009]
                       shadow-2xl shadow-black/50"
          >
            {/* inner glows */}
            <div className="absolute inset-0 pointer-events-none"
              style={{
                background:
                  "radial-gradient(ellipse 60% 80% at 20% 50%, rgba(16,185,129,0.12) 0%, transparent 60%)," +
                  "radial-gradient(ellipse 60% 80% at 80% 50%, rgba(5,150,105,0.08) 0%, transparent 60%)",
              }}
            />

            <div className="relative z-10">
              <h2 className="text-[32px] lg:text-[48px] font-black text-white tracking-tight mb-4 leading-tight">
                Start predicting smarter today
              </h2>
              <p className="text-[15px] text-[#6d9877] mb-10 max-w-lg mx-auto leading-relaxed">
                Connect your broker, search any Indian stock, and let our AI ensemble give you the edge.
              </p>
              <Link
                href="/sign-up"
                className="inline-flex items-center gap-2 px-9 py-4 rounded-xl
                           bg-white hover:bg-emerald-50
                           text-emerald-900 font-black text-[15px]
                           shadow-xl shadow-black/30
                           transition-all duration-200 hover:-translate-y-0.5"
              >
                Create Free Account <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ════════════════ FOOTER ════════════════ */}
      <footer className="border-t border-white/[0.04] py-8 px-6 lg:px-10">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-lg bg-emerald-600/20 flex items-center justify-center">
              <Leaf className="h-3 w-3 text-emerald-500" />
            </div>
            <span className="text-[13px] font-bold text-white">Finsight AI</span>
          </div>

          <p className="text-[12px] text-[#2d4d36]">
            © {new Date().getFullYear()} Finsight AI · Built for the Indian market · Not financial advice
          </p>

          <div className="flex items-center gap-5">
            <Link href="/sign-in"  className="text-[12px] text-[#4a6c54] hover:text-emerald-400 transition-colors">Sign In</Link>
            <Link href="/sign-up" className="text-[12px] text-[#4a6c54] hover:text-emerald-400 transition-colors">Sign Up</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
