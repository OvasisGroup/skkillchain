"use client";

import { ShieldCheck } from "lucide-react";
import { useState } from "react";
import { LoadingState } from "@/components/dashboard/DashboardStates";
import { ApiError } from "@/lib/api/client";
import { enrollMfa, verifyMfa } from "@/lib/api/auth";
import { ThemeToggle } from "@/components/ThemeToggle";
import { useAuth } from "@/lib/auth/AuthContext";
import { Reveal } from "@/components/animation/Reveal";

export default function SettingsPage() {
  const { user, accessToken } = useAuth();
  const [enrollment, setEnrollment] = useState<{ provisioning_uri: string; secret: string } | null>(
    null
  );
  const [code, setCode] = useState("");
  const [enrolling, setEnrolling] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [confirmed, setConfirmed] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!user || !accessToken) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-16">
        <LoadingState label="Loading settings…" />
      </div>
    );
  }

  async function handleStartEnroll() {
    setEnrolling(true);
    setError(null);
    try {
      const result = await enrollMfa(accessToken as string);
      setEnrollment(result);
      setConfirmed(false);
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't start two-factor setup.");
    } finally {
      setEnrolling(false);
    }
  }

  async function handleVerify(e: React.FormEvent) {
    e.preventDefault();
    setVerifying(true);
    setError(null);
    try {
      await verifyMfa(code, accessToken as string);
      setConfirmed(true);
      setEnrollment(null);
      setCode("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Invalid code — try again.");
    } finally {
      setVerifying(false);
    }
  }

  return (
    <Reveal className="mx-auto max-w-3xl px-6 py-16">
      <div>
        <p className="text-sm font-semibold uppercase tracking-wider text-lime-400">Account</p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          Settings
        </h1>
      </div>

      <section className="mt-10 rounded-2xl border border-border bg-surface p-6">
        <h2 className="text-lg font-semibold text-foreground">Appearance</h2>
        <div className="mt-4 flex items-center justify-between">
          <p className="text-sm text-foreground/60">Switch between light and dark mode.</p>
          <ThemeToggle />
        </div>
      </section>

      <section className="mt-6 rounded-2xl border border-border bg-surface p-6">
        <div className="flex items-center gap-2.5">
          <ShieldCheck className="h-5 w-5 text-teal-400" />
          <h2 className="text-lg font-semibold text-foreground">Two-factor authentication</h2>
        </div>
        <p className="mt-2 text-sm text-foreground/60">
          Add an extra layer of security to your account using an authenticator app.
        </p>

        {confirmed && (
          <p className="mt-4 text-sm text-emerald-400">Two-factor authentication is now enabled.</p>
        )}

        {!enrollment && !confirmed && (
          <button
            type="button"
            onClick={handleStartEnroll}
            disabled={enrolling}
            className="mt-4 rounded-full bg-teal-400 px-5 py-2 text-sm font-semibold text-emerald-950 transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {enrolling ? "Starting…" : "Set up two-factor authentication"}
          </button>
        )}

        {enrollment && (
          <div className="mt-4 space-y-4">
            <p className="text-sm text-foreground/70">
              Scan this in your authenticator app, or enter the secret manually:
            </p>
            <div className="rounded-lg border border-border-strong bg-background p-3 text-xs text-foreground/70">
              <p className="break-all">{enrollment.provisioning_uri}</p>
              <p className="mt-2 font-mono tracking-wider text-foreground">{enrollment.secret}</p>
            </div>

            <form onSubmit={handleVerify} className="flex items-end gap-3">
              <label className="block flex-1">
                <span className="text-sm font-medium text-foreground/80">Enter 6-digit code</span>
                <input
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  maxLength={6}
                  inputMode="numeric"
                  className="mt-1.5 w-full rounded-lg border border-border-strong bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-teal-400"
                />
              </label>
              <button
                type="submit"
                disabled={verifying || code.length !== 6}
                className="rounded-full bg-teal-400 px-5 py-2 text-sm font-semibold text-emerald-950 transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {verifying ? "Verifying…" : "Confirm"}
              </button>
            </form>
          </div>
        )}

        {error && <p className="mt-4 text-sm text-rose-400">{error}</p>}
      </section>
    </Reveal>
  );
}
