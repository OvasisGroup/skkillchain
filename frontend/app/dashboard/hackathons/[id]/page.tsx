"use client";

import { ArrowLeft, Trophy } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { DataTable } from "@/components/dashboard/DataTable";
import { ErrorState, LoadingState } from "@/components/dashboard/DashboardStates";
import { Panel } from "@/components/dashboard/Panel";
import { ApiError } from "@/lib/api/client";
import {
  cancelHackathon,
  declareHackathonWinner,
  getOrganizerHackathon,
  listHackathonRegistrations,
  publishHackathon,
} from "@/lib/api/organizerHackathons";
import type { HackathonOrganizerRegistration, HackathonWriteResult } from "@/lib/api/types";
import { useAuth } from "@/lib/auth/AuthContext";

const STATUS_STYLES: Record<string, string> = {
  draft: "bg-foreground/10 text-foreground/70",
  published: "bg-emerald-500/10 text-emerald-400",
  canceled: "bg-rose-500/10 text-rose-400",
};

export default function ManageHackathonPage() {
  const { id } = useParams<{ id: string }>();
  const { accessToken } = useAuth();

  const [hackathon, setHackathon] = useState<HackathonWriteResult | null>(null);
  const [registrations, setRegistrations] = useState<HackathonOrganizerRegistration[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [winnerBusyId, setWinnerBusyId] = useState<string | null>(null);
  const [placements, setPlacements] = useState<Record<string, string>>({});
  const [prizes, setPrizes] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!accessToken || !id) return;
    let cancelled = false;

    async function load() {
      const token = accessToken as string;
      const [detail, registrationsPage] = await Promise.all([
        getOrganizerHackathon(id, token),
        listHackathonRegistrations(id, token),
      ]);
      if (cancelled) return;
      setHackathon(detail);
      setRegistrations(registrationsPage.results);
    }

    load().catch((err) => {
      if (cancelled) return;
      setError(err instanceof ApiError ? err.message_ : "Couldn't load this hackathon.");
    });

    return () => {
      cancelled = true;
    };
  }, [accessToken, id]);

  async function handlePublish() {
    if (!accessToken || !hackathon) return;
    setBusy(true);
    try {
      const updated = await publishHackathon(hackathon.id, accessToken);
      setHackathon((prev) => (prev ? { ...prev, status: updated.status } : prev));
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't publish this hackathon.");
    } finally {
      setBusy(false);
    }
  }

  async function handleCancel() {
    if (!accessToken || !hackathon) return;
    setBusy(true);
    try {
      const updated = await cancelHackathon(hackathon.id, accessToken);
      setHackathon((prev) => (prev ? { ...prev, status: updated.status } : prev));
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't cancel this hackathon.");
    } finally {
      setBusy(false);
    }
  }

  async function handleDeclareWinner(registrationId: string) {
    if (!accessToken || !hackathon) return;
    const placement = Number(placements[registrationId] ?? "1");
    setWinnerBusyId(registrationId);
    setError(null);
    try {
      await declareHackathonWinner(
        hackathon.id,
        { registration_id: registrationId, placement, prize_description: prizes[registrationId] },
        accessToken
      );
      const registrationsPage = await listHackathonRegistrations(hackathon.id, accessToken);
      setRegistrations(registrationsPage.results);
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't declare this winner.");
    } finally {
      setWinnerBusyId(null);
    }
  }

  if (error) return <ErrorState message={error} />;
  if (!hackathon || !registrations) return <LoadingState label="Loading hackathon…" />;

  return (
    <div className="space-y-8">
      <div>
        <Link
          href="/dashboard/hackathons"
          className="flex items-center gap-1.5 text-sm text-foreground/50 hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" /> Back to hackathons
        </Link>
        <div className="mt-3 flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-semibold text-foreground sm:text-3xl">
                {hackathon.title}
              </h1>
              <span
                className={`rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${STATUS_STYLES[hackathon.status] ?? ""}`}
              >
                {hackathon.status}
              </span>
            </div>
            <p className="mt-1 text-sm text-foreground/50">
              {hackathon.host_type === "partner"
                ? `In partnership with ${hackathon.partner_name || "a partner organization"}`
                : "Hosted internally"}
            </p>
          </div>
          <div className="flex gap-2">
            {hackathon.status === "draft" && (
              <button
                type="button"
                onClick={handlePublish}
                disabled={busy}
                className="rounded-full bg-teal-400 px-4 py-1.5 text-sm font-semibold text-emerald-950 transition-opacity hover:opacity-90 disabled:opacity-50"
              >
                Publish
              </button>
            )}
            {hackathon.status !== "canceled" && (
              <button
                type="button"
                onClick={handleCancel}
                disabled={busy}
                className="rounded-full border border-border-strong px-4 py-1.5 text-sm font-semibold text-foreground/80 transition-colors hover:bg-surface-hover disabled:opacity-50"
              >
                Cancel
              </button>
            )}
            <Link
              href={`/hackathons/${hackathon.id}`}
              className="rounded-full border border-border-strong px-4 py-1.5 text-sm font-semibold text-foreground/80 transition-colors hover:bg-surface-hover"
            >
              View public page
            </Link>
          </div>
        </div>
      </div>

      <Panel title="Registrations & submissions">
        <DataTable
          rows={registrations}
          getRowKey={(r) => r.id}
          emptyMessage="No one has registered yet."
          columns={[
            { header: "Participant", cell: (r) => r.participant.email },
            { header: "Team", cell: (r) => r.team_name || "—" },
            {
              header: "Status",
              cell: (r) => <span className="capitalize">{r.status}</span>,
            },
            {
              header: "Submission",
              cell: (r) =>
                r.submission ? (
                  <a
                    href={r.submission.repo_url || r.submission.demo_url || undefined}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-teal-400 hover:underline"
                  >
                    {r.submission.title}
                  </a>
                ) : (
                  <span className="text-foreground/40">Not submitted</span>
                ),
            },
            {
              header: "Declare winner",
              cell: (r) =>
                r.submission ? (
                  <div className="flex items-center gap-1.5">
                    <input
                      type="number"
                      min={1}
                      placeholder="#"
                      value={placements[r.id] ?? ""}
                      onChange={(e) =>
                        setPlacements((prev) => ({ ...prev, [r.id]: e.target.value }))
                      }
                      className="w-14 rounded-lg border border-border-strong bg-surface px-2 py-1 text-xs"
                    />
                    <input
                      type="text"
                      placeholder="Prize"
                      value={prizes[r.id] ?? ""}
                      onChange={(e) => setPrizes((prev) => ({ ...prev, [r.id]: e.target.value }))}
                      className="w-28 rounded-lg border border-border-strong bg-surface px-2 py-1 text-xs"
                    />
                    <button
                      type="button"
                      onClick={() => handleDeclareWinner(r.id)}
                      disabled={winnerBusyId === r.id}
                      className="flex items-center gap-1 rounded-full bg-teal-400 px-3 py-1 text-xs font-semibold text-emerald-950 transition-opacity hover:opacity-90 disabled:opacity-50"
                    >
                      <Trophy className="h-3.5 w-3.5" />
                      {winnerBusyId === r.id ? "Saving…" : "Award"}
                    </button>
                  </div>
                ) : (
                  <span className="text-foreground/30">—</span>
                ),
            },
          ]}
        />
      </Panel>
    </div>
  );
}
