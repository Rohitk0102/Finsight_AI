"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Loader2, Link2, ExternalLink, CheckCircle2, Info } from "lucide-react";
import { apiClient } from "@/lib/api/client";

export default function SettingsPage() {
  const [zerodhaToken, setZerodhaToken] = useState("");
  const [angelClientId, setAngelClientId] = useState("");
  const [angelMpin, setAngelMpin] = useState("");
  const [angelTotp, setAngelTotp] = useState("");
  const [growwToken, setGrowwToken] = useState("");
  const [loading, setLoading] = useState<string | null>(null);

  const connectUpstox = async () => {
    setLoading("upstox");
    try {
      const res = await apiClient.get("/broker/upstox/authorize");
      // Backend already appends &state=USER_ID — do NOT append again here.
      window.location.href = res.data.auth_url;
    } catch {
      toast.error("Failed to get Upstox auth URL");
    } finally {
      setLoading(null);
    }
  };

  const connectZerodha = async () => {
    if (!zerodhaToken.trim()) { toast.error("Enter your request token"); return; }
    setLoading("zerodha");
    try {
      await apiClient.post(`/broker/zerodha/connect?request_token=${zerodhaToken}`);
      toast.success("Zerodha connected successfully!");
      setZerodhaToken("");
    } catch {
      toast.error("Zerodha connection failed");
    } finally {
      setLoading(null);
    }
  };

  const connectAngelOne = async () => {
    if (!angelClientId || !angelMpin || !angelTotp) {
      toast.error("Please fill in all Angel One fields");
      return;
    }
    setLoading("angel");
    try {
      await apiClient.post(
        `/broker/angelone/connect?client_id=${angelClientId}&mpin=${angelMpin}&totp=${angelTotp}`
      );
      toast.success("Angel One connected successfully!");
      setAngelClientId(""); setAngelMpin(""); setAngelTotp("");
    } catch {
      toast.error("Angel One connection failed");
    } finally {
      setLoading(null);
    }
  };

  const connectGroww = async () => {
    if (!growwToken.trim()) { toast.error("Enter your Groww access token"); return; }
    setLoading("groww");
    try {
      await apiClient.post(`/broker/groww/connect?access_token=${growwToken}`);
      toast.success("Groww connected successfully!");
      setGrowwToken("");
    } catch {
      toast.error("Groww connection failed");
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="max-w-2xl">
      <div className="mb-6">
        <h1 className="text-page-title">Settings</h1>
        <p className="text-body-sm text-muted-foreground mt-0.5">
          Connect your broker accounts to sync your portfolio
        </p>
      </div>

      <div className="space-y-4">
        {/* Upstox */}
        <BrokerCard
          name="Upstox"
          subtitle="OAuth2 · One-click secure connect"
          color="#7B68EE"
          badge="Recommended"
          index={0}
        >
          <p className="text-body-sm text-muted-foreground mb-4">
            Connect via Upstox OAuth2. You&apos;ll be redirected to Upstox to authorise access,
            then brought back automatically.
          </p>
          <button
            onClick={connectUpstox}
            disabled={loading === "upstox"}
            className="btn-primary px-5 py-2.5"
          >
            {loading === "upstox"
              ? <><Loader2 className="h-4 w-4 animate-spin" /> Connecting…</>
              : <><Link2 className="h-4 w-4" /> Connect with Upstox <ExternalLink className="h-3 w-3 opacity-60" /></>
            }
          </button>
        </BrokerCard>

        {/* Zerodha */}
        <BrokerCard
          name="Zerodha (Kite)"
          subtitle="Paste request token after Kite login"
          color="#387ED1"
          index={1}
        >
          <div className="mb-4">
            {process.env.NEXT_PUBLIC_ZERODHA_API_KEY && (
              <a
                href={`https://kite.zerodha.com/connect/login?api_key=${process.env.NEXT_PUBLIC_ZERODHA_API_KEY}`}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 text-[13px] font-medium mb-3 hover:underline"
                style={{ color: "hsl(var(--primary))" }}
              >
                <ExternalLink className="h-3.5 w-3.5" />
                Step 1: Open Kite Login page
              </a>
            )}

            <div
              className="flex items-start gap-2 rounded-xl p-3 mb-4 text-[12px]"
              style={{ background: "hsl(var(--primary) / 0.06)", color: "hsl(var(--muted-foreground))" }}
            >
              <Info className="h-3.5 w-3.5 flex-shrink-0 mt-0.5" style={{ color: "hsl(var(--primary))" }} />
              After login, copy the <code className="font-mono bg-muted px-1 rounded">request_token</code> from
              the redirect URL and paste it below.
            </div>

            <label className="text-label-xs text-muted-foreground mb-1.5 block font-medium">
              Request Token
            </label>
            <input
              value={zerodhaToken}
              onChange={(e) => setZerodhaToken(e.target.value)}
              placeholder="Paste request_token from redirect URL"
              className="input-field"
            />
          </div>
          <button
            onClick={connectZerodha}
            disabled={loading === "zerodha" || !zerodhaToken.trim()}
            className="btn-primary px-5 py-2.5"
          >
            {loading === "zerodha"
              ? <><Loader2 className="h-4 w-4 animate-spin" /> Connecting…</>
              : <><Link2 className="h-4 w-4" /> Connect Zerodha</>
            }
          </button>
        </BrokerCard>

        {/* Angel One */}
        <BrokerCard
          name="Angel One"
          subtitle="Login with Client ID + MPIN + TOTP"
          color="#E85D04"
          index={2}
        >
          <div className="space-y-3 mb-4">
            {[
              { label: "Client ID",                   value: angelClientId, setter: setAngelClientId, type: "text",     placeholder: "Your Angel One Client ID" },
              { label: "MPIN",                         value: angelMpin,     setter: setAngelMpin,     type: "password", placeholder: "4–6 digit MPIN" },
              { label: "TOTP (Google Authenticator)",  value: angelTotp,     setter: setAngelTotp,     type: "text",     placeholder: "6-digit TOTP code" },
            ].map(({ label, value, setter, type, placeholder }) => (
              <div key={label}>
                <label className="text-label-xs text-muted-foreground mb-1.5 block font-medium">{label}</label>
                <input
                  value={value}
                  onChange={(e) => setter(e.target.value)}
                  type={type}
                  placeholder={placeholder}
                  className="input-field"
                />
              </div>
            ))}
          </div>
          <button
            onClick={connectAngelOne}
            disabled={loading === "angel"}
            className="btn-primary px-5 py-2.5"
          >
            {loading === "angel"
              ? <><Loader2 className="h-4 w-4 animate-spin" /> Connecting…</>
              : <><Link2 className="h-4 w-4" /> Connect Angel One</>
            }
          </button>
        </BrokerCard>

        {/* Groww */}
        <BrokerCard
          name="Groww"
          subtitle="CSV import · No official API"
          color="#00D09C"
          badge="CSV Only"
          index={3}
        >
          <div
            className="flex items-start gap-3 rounded-xl p-4"
            style={{ background: "hsl(var(--muted))" }}
          >
            <Info className="h-4 w-4 flex-shrink-0 mt-0.5 text-muted-foreground" />
            <div className="text-body-sm text-muted-foreground">
              <p className="font-medium text-foreground mb-1">How to import from Groww</p>
              <ol className="space-y-1 text-[12px]">
                <li>1. Open Groww app → Portfolio</li>
                <li>2. Tap ··· → Export as CSV</li>
                <li>3. Upload the CSV in the Portfolio page</li>
              </ol>
            </div>
          </div>
        </BrokerCard>

        {/* Security note */}
        <div
          className="flex items-start gap-3 rounded-2xl p-4 border animate-slide-in-up delay-300"
          style={{
            background: "hsl(var(--primary) / 0.04)",
            borderColor: "hsl(var(--primary) / 0.15)",
          }}
        >
          <CheckCircle2 className="h-4 w-4 flex-shrink-0 mt-0.5" style={{ color: "hsl(var(--primary))" }} />
          <div>
            <p className="text-[13px] font-medium mb-0.5" style={{ color: "hsl(var(--primary))" }}>
              Your credentials are secure
            </p>
            <p className="text-[12px] text-muted-foreground">
              All broker tokens are encrypted with AES-256 (Fernet) before storage.
              We never store your passwords.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

function BrokerCard({
  name, subtitle, color, badge, index, children,
}: {
  name: string; subtitle: string; color: string;
  badge?: string; index: number;
  children: React.ReactNode;
}) {
  return (
    <div
      className={`card-surface p-5 animate-slide-in-up`}
      style={{ animationDelay: `${index * 60}ms` }}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center font-bold text-[13px] flex-shrink-0"
            style={{ background: color + "18", color }}
          >
            {name.slice(0, 2).toUpperCase()}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-card-title font-semibold">{name}</h3>
              {badge && (
                <span
                  className="text-[10px] font-semibold px-2 py-0.5 rounded-full"
                  style={{ background: color + "18", color }}
                >
                  {badge}
                </span>
              )}
            </div>
            <p className="text-label-xs text-muted-foreground">{subtitle}</p>
          </div>
        </div>
      </div>

      <div
        className="w-full h-px mb-4"
        style={{ background: "hsl(var(--border))" }}
      />

      {children}
    </div>
  );
}
