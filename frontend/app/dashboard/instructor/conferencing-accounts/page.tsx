"use client";

import { AlertCircle, CheckCircle2, Trash2, Video } from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { ArrowLeft } from "lucide-react";
import { ErrorState, LoadingState } from "@/components/dashboard/DashboardStates";
import { PageHeader } from "@/components/dashboard/PageHeader";
import { ApiError } from "@/lib/api/client";
import {
  connectConferencingAccount,
  listConferencingAccounts,
  revokeConferencingAccount,
} from "@/lib/api/liveSessions";
import type { ConferencingAccount, ConferencingProvider } from "@/lib/api/types";
import { useAuth } from "@/lib/auth/AuthContext";

const PROVIDERS: { id: ConferencingProvider; label: string }[] = [
  { id: "zoom", label: "Zoom" },
  { id: "google_meet", label: "Google Meet" },
];

const CALLBACK_ERROR_MESSAGES: Record<string, string> = {
  invalid_state: "That connection request expired or was tampered with — please try again.",
  unknown_provider: "Unknown conferencing provider.",
  token_exchange_failed: "The provider rejected the connection — please try again.",
};

export default function ConferencingAccountsPage() {
  return (
    <Suspense>
      <ConferencingAccountsContent />
    </Suspense>
  );
}

function ConferencingAccountsContent() {
  const { accessToken } = useAuth();
  const searchParams = useSearchParams();
  const connected = searchParams.get("connected");
  const callbackError = searchParams.get("error");

  const [accounts, setAccounts] = useState<ConferencingAccount[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [connectingProvider, setConnectingProvider] = useState<ConferencingProvider | null>(null);
  const [revokingId, setRevokingId] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken) return;
    let cancelled = false;
    listConferencingAccounts(accessToken)
      .then((data) => {
        if (!cancelled) setAccounts(data);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message_ : "Couldn't load conferencing accounts.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [accessToken]);

  async function handleConnect(provider: ConferencingProvider) {
    if (!accessToken) return;
    setConnectingProvider(provider);
    setError(null);
    try {
      const { authorization_url } = await connectConferencingAccount(provider, accessToken);
      window.location.assign(authorization_url);
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't start the connection.");
      setConnectingProvider(null);
    }
  }

  async function handleRevoke(accountId: string) {
    if (!accessToken) return;
    setRevokingId(accountId);
    try {
      await revokeConferencingAccount(accountId, accessToken);
      setAccounts((prev) => prev?.filter((a) => a.id !== accountId) ?? prev);
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't disconnect this account.");
    } finally {
      setRevokingId(null);
    }
  }

  if (error && !accounts) return <ErrorState message={error} />;
  if (!accounts) return <LoadingState label="Loading conferencing accounts…" />;

  const connectedProviders = new Set(accounts.map((a) => a.provider));

  return (
    <div className="space-y-6">
      <div>
        <Link
          href="/dashboard/instructor"
          className="flex items-center gap-1.5 text-sm text-foreground/50 hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" /> Back to dashboard
        </Link>
      </div>
      <PageHeader
        eyebrow="Live sessions"
        title="Conferencing accounts"
        subtitle="Connect a Zoom or Google Meet account to schedule live sessions for your courses."
      />

      {connected && (
        <div className="flex items-start gap-2 rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-4 text-sm text-emerald-400">
          <CheckCircle2 className="mt-0.5 h-4 w-4 flex-none" />
          <span>
            {PROVIDERS.find((p) => p.id === connected)?.label ?? connected} connected successfully.
          </span>
        </div>
      )}
      {callbackError && (
        <div className="flex items-start gap-2 rounded-xl border border-rose-500/20 bg-rose-500/10 p-4 text-sm text-rose-400">
          <AlertCircle className="mt-0.5 h-4 w-4 flex-none" />
          <span>{CALLBACK_ERROR_MESSAGES[callbackError] ?? "Couldn't connect that account."}</span>
        </div>
      )}
      {error && <p className="text-sm text-rose-400">{error}</p>}

      <div className="space-y-3">
        {PROVIDERS.map((provider) => {
          const account = accounts.find((a) => a.provider === provider.id);
          return (
            <div
              key={provider.id}
              className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border bg-surface p-4"
            >
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 flex-none items-center justify-center rounded-full bg-teal-400/10">
                  <Video className="h-5 w-5 text-teal-400" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-foreground">{provider.label}</p>
                  {account ? (
                    <p className="text-xs text-foreground/50">
                      Connected {new Date(account.connected_at).toLocaleDateString()}
                      {account.external_account_id ? ` · ${account.external_account_id}` : ""}
                    </p>
                  ) : (
                    <p className="text-xs text-foreground/40">Not connected</p>
                  )}
                </div>
              </div>

              {account ? (
                <button
                  type="button"
                  onClick={() => handleRevoke(account.id)}
                  disabled={revokingId === account.id}
                  className="flex items-center gap-1.5 rounded-full border border-border-strong px-3 py-1.5 text-xs font-semibold text-foreground/70 transition-colors hover:bg-surface-hover disabled:opacity-50"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                  {revokingId === account.id ? "Disconnecting…" : "Disconnect"}
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => handleConnect(provider.id)}
                  disabled={connectingProvider === provider.id || connectedProviders.has(provider.id)}
                  className="rounded-full bg-teal-400 px-4 py-1.5 text-xs font-semibold text-emerald-950 transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {connectingProvider === provider.id ? "Redirecting…" : `Connect ${provider.label}`}
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
