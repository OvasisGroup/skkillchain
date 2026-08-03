"use client";

import { ChevronDown, ChevronUp, Plus } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { authInputClass } from "@/components/AuthCard";
import { DataTable } from "@/components/dashboard/DataTable";
import { ApiError } from "@/lib/api/client";
import {
  cancelLiveSession,
  listConferencingAccounts,
  listCourseLiveSessions,
  listLiveSessionRegistrations,
  scheduleLiveSession,
} from "@/lib/api/liveSessions";
import type {
  ConferencingAccount,
  LiveSession,
  LiveSessionRegistration,
} from "@/lib/api/types";

const STATUS_STYLES: Record<LiveSession["status"], string> = {
  scheduled: "bg-teal-400/10 text-teal-400",
  live: "bg-emerald-500/10 text-emerald-400",
  ended: "bg-foreground/10 text-foreground/50",
  canceled: "bg-rose-500/10 text-rose-400",
};

function RegistrationsPanel({ sessionId, token }: { sessionId: string; token: string }) {
  const [registrations, setRegistrations] = useState<LiveSessionRegistration[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    listLiveSessionRegistrations(sessionId, token)
      .then((data) => {
        if (!cancelled) setRegistrations(data);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message_ : "Couldn't load registrations.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [sessionId, token]);

  if (error) return <p className="mt-3 text-xs text-rose-400">{error}</p>;
  if (!registrations) return <p className="mt-3 text-xs text-foreground/50">Loading registrations…</p>;

  return (
    <div className="mt-3">
      <DataTable
        rows={registrations}
        getRowKey={(r) => r.id}
        emptyMessage="No one has registered yet."
        columns={[
          { header: "Student", cell: (r) => r.student_email },
          { header: "Status", cell: (r) => <span className="capitalize">{r.status}</span> },
          {
            header: "Joined",
            cell: (r) => (r.joined_at ? new Date(r.joined_at).toLocaleString() : "—"),
          },
        ]}
      />
    </div>
  );
}

function ScheduleSessionForm({
  courseId,
  token,
  accounts,
  onCreated,
  onCancel,
}: {
  courseId: string;
  token: string;
  accounts: ConferencingAccount[];
  onCreated: (session: LiveSession) => void;
  onCancel: () => void;
}) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [accountId, setAccountId] = useState(accounts[0]?.id ?? "");
  const [startAt, setStartAt] = useState("");
  const [endAt, setEndAt] = useState("");
  const [capacity, setCapacity] = useState("");
  const [isRecorded, setIsRecorded] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedAccount = accounts.find((a) => a.id === accountId);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!title.trim() || !startAt || !endAt || !selectedAccount) return;
    setSubmitting(true);
    setError(null);
    try {
      const session = await scheduleLiveSession(
        courseId,
        {
          conferencing_account_id: selectedAccount.id,
          provider: selectedAccount.provider,
          title,
          description,
          scheduled_start_at: new Date(startAt).toISOString(),
          scheduled_end_at: new Date(endAt).toISOString(),
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
          capacity: capacity ? Number(capacity) : undefined,
          is_recorded: isRecorded,
        },
        token
      );
      onCreated(session);
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't schedule this session.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="mt-3 space-y-3 rounded-lg border border-border-strong bg-background/40 p-3"
    >
      <input
        type="text"
        required
        autoFocus
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="Session title"
        className={authInputClass}
      />
      <textarea
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        placeholder="Description (optional)"
        rows={2}
        className={authInputClass}
      />
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        <div>
          <label className="block text-xs font-medium text-foreground/60">Starts</label>
          <input
            type="datetime-local"
            required
            value={startAt}
            onChange={(e) => setStartAt(e.target.value)}
            className={`mt-1 ${authInputClass}`}
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-foreground/60">Ends</label>
          <input
            type="datetime-local"
            required
            value={endAt}
            onChange={(e) => setEndAt(e.target.value)}
            className={`mt-1 ${authInputClass}`}
          />
        </div>
      </div>
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
        <div className="sm:col-span-2">
          <label className="block text-xs font-medium text-foreground/60">Conferencing account</label>
          <select
            value={accountId}
            onChange={(e) => setAccountId(e.target.value)}
            className={`mt-1 ${authInputClass}`}
          >
            {accounts.map((account) => (
              <option key={account.id} value={account.id}>
                {account.provider === "zoom" ? "Zoom" : "Google Meet"}
                {account.external_account_id ? ` · ${account.external_account_id}` : ""}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-foreground/60">Capacity</label>
          <input
            type="number"
            min="1"
            value={capacity}
            onChange={(e) => setCapacity(e.target.value)}
            placeholder="Unlimited"
            className={`mt-1 ${authInputClass}`}
          />
        </div>
      </div>
      <label className="flex items-center gap-2 text-sm text-foreground/70">
        <input
          type="checkbox"
          checked={isRecorded}
          onChange={(e) => setIsRecorded(e.target.checked)}
          className="h-4 w-4 rounded border-border-strong"
        />
        Record this session
      </label>
      {error && <p className="text-sm text-rose-400">{error}</p>}
      <div className="flex gap-2">
        <button
          type="submit"
          disabled={submitting || !title.trim() || !startAt || !endAt}
          className="rounded-full bg-teal-400 px-4 py-1.5 text-xs font-semibold text-emerald-950 transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {submitting ? "Scheduling…" : "Schedule session"}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="text-xs text-foreground/50 hover:text-foreground"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}

export function LiveSessionsBuilder({ courseId, token }: { courseId: string; token: string }) {
  const [sessions, setSessions] = useState<LiveSession[] | null>(null);
  const [accounts, setAccounts] = useState<ConferencingAccount[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([listCourseLiveSessions(courseId), listConferencingAccounts(token)])
      .then(([sessionsData, accountsData]) => {
        if (cancelled) return;
        setSessions(sessionsData);
        setAccounts(accountsData);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message_ : "Couldn't load live sessions.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [courseId, token]);

  async function handleCancel(sessionId: string) {
    setBusyId(sessionId);
    try {
      const updated = await cancelLiveSession(sessionId, token);
      setSessions((prev) => prev?.map((s) => (s.id === sessionId ? updated : s)) ?? prev);
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't cancel this session.");
    } finally {
      setBusyId(null);
    }
  }

  if (error && !sessions) return <p className="text-sm text-rose-400">{error}</p>;
  if (!sessions || !accounts) return <p className="text-sm text-foreground/50">Loading live sessions…</p>;

  if (accounts.length === 0) {
    return (
      <p className="text-sm text-foreground/50">
        Connect a Zoom or Google Meet account before scheduling live sessions —{" "}
        <Link
          href="/dashboard/instructor/conferencing-accounts"
          className="text-teal-400 hover:underline"
        >
          connect one now
        </Link>
        .
      </p>
    );
  }

  return (
    <div className="space-y-4">
      {error && <p className="text-sm text-rose-400">{error}</p>}

      {sessions.length === 0 && !showForm && (
        <p className="text-sm text-foreground/50">No live sessions scheduled yet.</p>
      )}

      {sessions.length > 0 && (
        <div className="space-y-2">
          {sessions.map((session) => (
            <div key={session.id} className="rounded-xl border border-border bg-surface p-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <p className="font-medium text-foreground">{session.title}</p>
                  <p className="text-xs text-foreground/50">
                    {new Date(session.scheduled_start_at).toLocaleString()} –{" "}
                    {new Date(session.scheduled_end_at).toLocaleTimeString()}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className={`rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${STATUS_STYLES[session.status]}`}
                  >
                    {session.status}
                  </span>
                  {session.status === "scheduled" && (
                    <button
                      type="button"
                      onClick={() => handleCancel(session.id)}
                      disabled={busyId === session.id}
                      className="rounded-full border border-border-strong px-3 py-1 text-xs font-semibold text-foreground/80 transition-colors hover:bg-surface-hover disabled:opacity-50"
                    >
                      {busyId === session.id ? "Canceling…" : "Cancel"}
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => setExpandedId(expandedId === session.id ? null : session.id)}
                    className="flex items-center gap-1 text-xs font-semibold text-teal-400 hover:text-teal-300"
                  >
                    Registrations
                    {expandedId === session.id ? (
                      <ChevronUp className="h-3.5 w-3.5" />
                    ) : (
                      <ChevronDown className="h-3.5 w-3.5" />
                    )}
                  </button>
                </div>
              </div>
              {expandedId === session.id && (
                <RegistrationsPanel sessionId={session.id} token={token} />
              )}
            </div>
          ))}
        </div>
      )}

      {showForm ? (
        <ScheduleSessionForm
          courseId={courseId}
          token={token}
          accounts={accounts}
          onCreated={(session) => {
            setSessions((prev) => [...(prev ?? []), session]);
            setShowForm(false);
          }}
          onCancel={() => setShowForm(false)}
        />
      ) : (
        <button
          type="button"
          onClick={() => setShowForm(true)}
          className="flex items-center gap-1 text-xs font-semibold text-teal-400 hover:text-teal-300"
        >
          <Plus className="h-3.5 w-3.5" /> Schedule session
        </button>
      )}
    </div>
  );
}
