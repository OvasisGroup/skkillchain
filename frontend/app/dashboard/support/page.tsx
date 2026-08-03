"use client";

import { AlertOctagon, LifeBuoy } from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { DataTable } from "@/components/dashboard/DataTable";
import { ErrorState, LoadingState } from "@/components/dashboard/DashboardStates";
import { PageHeader } from "@/components/dashboard/PageHeader";
import { Panel } from "@/components/dashboard/Panel";
import { StatCard } from "@/components/dashboard/StatCard";
import { ApiError } from "@/lib/api/client";
import { listAdminTickets, updateAdminTicket } from "@/lib/api/support";
import type { SupportTicket } from "@/lib/api/types";
import { useAuth } from "@/lib/auth/AuthContext";

const STATUS_OPTIONS: SupportTicket["status"][] = ["open", "in_progress", "resolved", "closed"];
const STATUS_STYLES: Record<SupportTicket["status"], string> = {
  open: "bg-amber-500/10 text-amber-400",
  in_progress: "bg-teal-400/10 text-teal-400",
  resolved: "bg-emerald-500/10 text-emerald-400",
  closed: "bg-foreground/10 text-foreground/50",
};

export default function SupportDashboardPage() {
  const { accessToken, user } = useAuth();
  const [tickets, setTickets] = useState<SupportTicket[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [busyId, setBusyId] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken) return;
    let cancelled = false;
    listAdminTickets(accessToken)
      .then((data) => {
        if (!cancelled) setTickets(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof ApiError ? err.message_ : "Couldn't load tickets.");
      });
    return () => {
      cancelled = true;
    };
  }, [accessToken]);

  const filtered = useMemo(() => {
    if (!tickets) return [];
    return statusFilter === "all" ? tickets : tickets.filter((t) => t.status === statusFilter);
  }, [tickets, statusFilter]);

  async function handleUpdate(ticketId: string, patch: Partial<SupportTicket>) {
    if (!accessToken) return;
    setBusyId(ticketId);
    try {
      const updated = await updateAdminTicket(ticketId, patch, accessToken);
      setTickets((prev) => prev?.map((t) => (t.id === ticketId ? updated : t)) ?? prev);
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't update this ticket.");
    } finally {
      setBusyId(null);
    }
  }

  if (error) return <ErrorState message={error} />;
  if (!tickets) return <LoadingState label="Loading support tickets…" />;

  const openCount = tickets.filter((t) => t.status === "open").length;
  const breachedCount = tickets.filter((t) => t.is_sla_breached).length;

  return (
    <div className="space-y-8">
      <PageHeader title="Support" />

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard label="Total tickets" value={String(tickets.length)} icon={LifeBuoy} />
        <StatCard label="Open" value={String(openCount)} icon={LifeBuoy} />
        <StatCard label="SLA breached" value={String(breachedCount)} icon={AlertOctagon} />
      </div>

      <Panel
        title="Tickets"
        actions={
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-lg border border-border-strong bg-surface px-3 py-1.5 text-sm text-foreground focus:border-teal-400 focus:outline-none"
          >
            <option value="all">All statuses</option>
            {STATUS_OPTIONS.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        }
      >
        <DataTable
          rows={filtered}
          getRowKey={(t) => t.id}
          emptyMessage="No tickets match this filter."
          columns={[
            {
              header: "Subject",
              cell: (t) => (
                <Link href={`/dashboard/support/${t.id}`} className="text-teal-400 hover:underline">
                  {t.subject}
                </Link>
              ),
            },
            { header: "Category", cell: (t) => <span className="capitalize">{t.category}</span> },
            { header: "Priority", cell: (t) => <span className="capitalize">{t.priority}</span> },
            {
              header: "Status",
              cell: (t) => (
                <select
                  value={t.status}
                  disabled={busyId === t.id}
                  onChange={(e) =>
                    handleUpdate(t.id, { status: e.target.value as SupportTicket["status"] })
                  }
                  className={`rounded-full border-0 px-2.5 py-0.5 text-xs font-medium capitalize ${STATUS_STYLES[t.status]}`}
                >
                  {STATUS_OPTIONS.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              ),
            },
            {
              header: "Assignee",
              cell: (t) =>
                t.assignee === user?.id ? (
                  <span className="text-xs text-foreground/50">You</span>
                ) : t.assignee ? (
                  <span className="text-xs text-foreground/50">Assigned</span>
                ) : (
                  <button
                    type="button"
                    disabled={busyId === t.id}
                    onClick={() => user && handleUpdate(t.id, { assignee: user.id })}
                    className="rounded-full border border-border-strong px-2.5 py-1 text-xs font-semibold text-foreground/80 hover:bg-surface-hover disabled:opacity-50"
                  >
                    Assign to me
                  </button>
                ),
            },
          ]}
        />
      </Panel>
    </div>
  );
}
