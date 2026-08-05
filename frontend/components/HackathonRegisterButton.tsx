"use client";

import { CheckCircle2, Loader2 } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { ApiError } from "@/lib/api/client";
import { listMyHackathonRegistrations, registerForHackathon } from "@/lib/api/hackathons";
import type { HackathonDetail } from "@/lib/api/types";
import { useAuth } from "@/lib/auth/AuthContext";

export function HackathonRegisterButton({ hackathon }: { hackathon: HackathonDetail }) {
  const { isAuthenticated, accessToken } = useAuth();
  const [status, setStatus] = useState<"idle" | "loading" | "registered" | "error">("idle");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken) return;
    let cancelled = false;
    listMyHackathonRegistrations(accessToken)
      .then((page) => {
        const active = page.results.some(
          (r) => r.hackathon.id === hackathon.id && r.status === "registered"
        );
        if (!cancelled && active) setStatus("registered");
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [accessToken, hackathon.id]);

  if (!isAuthenticated) {
    return (
      <Link
        href={`/register?next=${encodeURIComponent(`/hackathons/${hackathon.id}`)}`}
        className="block w-full rounded-full bg-teal-400 px-6 py-3.5 text-center text-sm font-semibold text-emerald-950 shadow-sm shadow-teal-500/20 transition-opacity hover:opacity-90"
      >
        Sign up to register
      </Link>
    );
  }

  if (status === "registered") {
    return (
      <div className="flex w-full items-center justify-center gap-2 rounded-full bg-emerald-500/10 px-6 py-3.5 text-sm font-semibold text-emerald-400">
        <CheckCircle2 className="h-4 w-4" />
        You&apos;re registered
      </div>
    );
  }

  if (!hackathon.is_registration_open) {
    return (
      <div className="w-full rounded-full bg-foreground/10 px-6 py-3.5 text-center text-sm font-semibold text-foreground/50">
        Registration closed
      </div>
    );
  }

  async function handleRegister() {
    if (!accessToken) return;
    setStatus("loading");
    setError(null);
    try {
      await registerForHackathon(hackathon.id, {}, accessToken);
      setStatus("registered");
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Something went wrong. Please try again.");
      setStatus("error");
    }
  }

  return (
    <div>
      <button
        type="button"
        onClick={handleRegister}
        disabled={status === "loading"}
        className="flex w-full items-center justify-center gap-2 rounded-full bg-teal-400 px-6 py-3.5 text-sm font-semibold text-emerald-950 shadow-sm shadow-teal-500/20 transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {status === "loading" && <Loader2 className="h-4 w-4 animate-spin" />}
        {status === "loading" ? "Registering…" : "Register to compete"}
      </button>
      {error && <p className="mt-2 text-center text-xs text-red-400">{error}</p>}
    </div>
  );
}
