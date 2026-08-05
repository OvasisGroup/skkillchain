"use client";

import { Plus, Trophy } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { authInputClass } from "@/components/AuthCard";
import { DataTable } from "@/components/dashboard/DataTable";
import { ErrorState, LoadingState } from "@/components/dashboard/DashboardStates";
import { PageHeader } from "@/components/dashboard/PageHeader";
import { Panel } from "@/components/dashboard/Panel";
import { ApiError } from "@/lib/api/client";
import { listMyHackathonRegistrations, submitHackathonProject } from "@/lib/api/hackathons";
import { listOrganizerHackathons } from "@/lib/api/organizerHackathons";
import type { Hackathon, HackathonRegistration } from "@/lib/api/types";
import { useAuth } from "@/lib/auth/AuthContext";

const STATUS_STYLES: Record<string, string> = {
  draft: "bg-foreground/10 text-foreground/70",
  published: "bg-emerald-500/10 text-emerald-400",
  canceled: "bg-rose-500/10 text-rose-400",
};

const REGISTRATION_STATUS_STYLES: Record<string, string> = {
  registered: "bg-emerald-500/10 text-emerald-400",
  withdrawn: "bg-foreground/10 text-foreground/50",
  disqualified: "bg-rose-500/10 text-rose-400",
};

export default function HackathonsDashboardPage() {
  const { accessToken } = useAuth();
  const [hosted, setHosted] = useState<Hackathon[] | null>(null);
  const [registrations, setRegistrations] = useState<HackathonRegistration[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitFormId, setSubmitFormId] = useState<string | null>(null);
  const [submitTitle, setSubmitTitle] = useState("");
  const [submitRepoUrl, setSubmitRepoUrl] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!accessToken) return;
    let cancelled = false;

    async function load() {
      const token = accessToken as string;
      const [hostedPage, registrationsPage] = await Promise.all([
        listOrganizerHackathons(token),
        listMyHackathonRegistrations(token),
      ]);
      if (cancelled) return;
      setHosted(hostedPage.results);
      setRegistrations(registrationsPage.results);
    }

    load().catch((err) => {
      if (cancelled) return;
      setError(err instanceof ApiError ? err.message_ : "Couldn't load your hackathons.");
    });

    return () => {
      cancelled = true;
    };
  }, [accessToken]);

  async function handleSubmitProject(hackathonId: string) {
    if (!accessToken || !submitTitle.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      await submitHackathonProject(
        hackathonId,
        { title: submitTitle, repo_url: submitRepoUrl },
        accessToken
      );
      const page = await listMyHackathonRegistrations(accessToken);
      setRegistrations(page.results);
      setSubmitFormId(null);
      setSubmitTitle("");
      setSubmitRepoUrl("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't submit your project.");
    } finally {
      setSubmitting(false);
    }
  }

  if (error) return <ErrorState message={error} />;
  if (!hosted || !registrations) return <LoadingState label="Loading your hackathons…" />;

  return (
    <div className="space-y-8">
      <PageHeader
        title="Hackathons"
        subtitle="Host a hackathon internally or with a partner organization, and track the ones you've registered for."
        actions={
          <Link
            href="/dashboard/hackathons/new"
            className="flex items-center gap-1.5 rounded-full bg-teal-400 px-4 py-1.5 text-sm font-semibold text-emerald-950 transition-opacity hover:opacity-90"
          >
            <Plus className="h-4 w-4" /> New hackathon
          </Link>
        }
      />

      <Panel title="Hackathons I'm hosting">
        <DataTable
          rows={hosted}
          getRowKey={(h) => h.id}
          emptyMessage="You haven't posted any hackathons yet."
          columns={[
            {
              header: "Title",
              cell: (h) => (
                <Link
                  href={`/dashboard/hackathons/${h.id}`}
                  className="font-medium text-foreground hover:text-teal-400"
                >
                  {h.title}
                </Link>
              ),
            },
            {
              header: "Host",
              cell: (h) => (h.host_type === "partner" ? h.partner_name || "Partner" : "Internal"),
            },
            {
              header: "Status",
              cell: (h) => (
                <span
                  className={`rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${STATUS_STYLES[h.status] ?? ""}`}
                >
                  {h.status}
                </span>
              ),
            },
            {
              header: "",
              cell: (h) => (
                <Link
                  href={`/dashboard/hackathons/${h.id}`}
                  className="rounded-full border border-border-strong px-3 py-1 text-xs font-semibold text-foreground/80 transition-colors hover:bg-surface-hover"
                >
                  Manage
                </Link>
              ),
            },
          ]}
        />
      </Panel>

      <Panel title="My registrations">
        <DataTable
          rows={registrations}
          getRowKey={(r) => r.id}
          emptyMessage="You haven't registered for any hackathons yet."
          columns={[
            {
              header: "Hackathon",
              cell: (r) => (
                <Link
                  href={`/hackathons/${r.hackathon.id}`}
                  className="font-medium text-foreground hover:text-teal-400"
                >
                  {r.hackathon.title}
                </Link>
              ),
            },
            {
              header: "Status",
              cell: (r) => (
                <span
                  className={`rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${REGISTRATION_STATUS_STYLES[r.status] ?? ""}`}
                >
                  {r.status}
                </span>
              ),
            },
            {
              header: "Submission",
              cell: (r) =>
                r.submission ? (
                  <span className="flex items-center gap-1.5 text-emerald-400">
                    <Trophy className="h-3.5 w-3.5" /> {r.submission.title}
                  </span>
                ) : r.status === "registered" ? (
                  <button
                    type="button"
                    onClick={() => setSubmitFormId(r.hackathon.id)}
                    className="rounded-full border border-border-strong px-3 py-1 text-xs font-semibold text-foreground/80 transition-colors hover:bg-surface-hover"
                  >
                    Submit project
                  </button>
                ) : (
                  <span className="text-foreground/40">—</span>
                ),
            },
          ]}
        />

        {submitFormId && (
          <div className="mt-4 space-y-3 rounded-xl border border-border bg-background/40 p-4">
            <p className="text-sm font-medium text-foreground">Submit your project</p>
            <input
              type="text"
              placeholder="Project title"
              value={submitTitle}
              onChange={(e) => setSubmitTitle(e.target.value)}
              className={authInputClass}
            />
            <input
              type="url"
              placeholder="Repository URL (optional)"
              value={submitRepoUrl}
              onChange={(e) => setSubmitRepoUrl(e.target.value)}
              className={authInputClass}
            />
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => handleSubmitProject(submitFormId)}
                disabled={submitting || !submitTitle.trim()}
                className="rounded-full bg-teal-400 px-4 py-1.5 text-sm font-semibold text-emerald-950 transition-opacity hover:opacity-90 disabled:opacity-50"
              >
                {submitting ? "Submitting…" : "Submit"}
              </button>
              <button
                type="button"
                onClick={() => setSubmitFormId(null)}
                className="rounded-full border border-border-strong px-4 py-1.5 text-sm font-semibold text-foreground/80 transition-colors hover:bg-surface-hover"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </Panel>
    </div>
  );
}
