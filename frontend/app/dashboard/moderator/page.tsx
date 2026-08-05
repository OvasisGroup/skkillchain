"use client";

import { useEffect, useState } from "react";
import { DataTable } from "@/components/dashboard/DataTable";
import { ErrorState, LoadingState } from "@/components/dashboard/DashboardStates";
import { PageHeader } from "@/components/dashboard/PageHeader";
import { Panel } from "@/components/dashboard/Panel";
import { StatCard } from "@/components/dashboard/StatCard";
import { ApiError } from "@/lib/api/client";
import { approveInstructorApplication, listInstructorApplications } from "@/lib/api/moderation";
import type { InstructorApplication } from "@/lib/api/types";
import { useAuth } from "@/lib/auth/AuthContext";
import { UserCheck } from "lucide-react";
import { Reveal } from "@/components/animation/Reveal";

export default function ModeratorDashboardPage() {
  const { accessToken } = useAuth();
  const [applications, setApplications] = useState<InstructorApplication[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken) return;
    let cancelled = false;
    listInstructorApplications(accessToken)
      .then((page) => {
        if (!cancelled) setApplications(page.results);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message_ : "Couldn't load instructor applications.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [accessToken]);

  async function handleApprove(userId: string) {
    if (!accessToken) return;
    setBusyId(userId);
    try {
      const updated = await approveInstructorApplication(userId, accessToken);
      setApplications((prev) => prev?.map((a) => (a.user === userId ? updated : a)) ?? prev);
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't approve this application.");
    } finally {
      setBusyId(null);
    }
  }

  if (error) return <ErrorState message={error} />;
  if (!applications) return <LoadingState label="Loading instructor applications…" />;

  const pendingCount = applications.filter((a) => a.status === "pending").length;

  return (
    <div className="space-y-8">
      <PageHeader title="Moderator" />

      <Reveal className="grid grid-cols-2 gap-4 sm:grid-cols-4" stagger={0.08}>
        <StatCard label="Pending applications" value={String(pendingCount)} icon={UserCheck} />
        <StatCard label="Total applications" value={String(applications.length)} icon={UserCheck} />
      </Reveal>

      <Panel title="Instructor applications">
        <DataTable
          rows={applications}
          getRowKey={(a) => a.id}
          emptyMessage="No instructor applications yet."
          columns={[
            { header: "Applicant", cell: (a) => a.user_email },
            {
              header: "Status",
              cell: (a) => (
                <span
                  className={`rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${
                    a.status === "approved"
                      ? "bg-emerald-500/10 text-emerald-400"
                      : "bg-amber-500/10 text-amber-400"
                  }`}
                >
                  {a.status}
                </span>
              ),
            },
            { header: "Applied", cell: (a) => new Date(a.applied_at).toLocaleDateString() },
            {
              header: "",
              cell: (a) =>
                a.status === "pending" ? (
                  <button
                    type="button"
                    onClick={() => handleApprove(a.user)}
                    disabled={busyId === a.user}
                    className="rounded-full bg-teal-400 px-3 py-1 text-xs font-semibold text-emerald-950 transition-opacity hover:opacity-90 disabled:opacity-50"
                  >
                    {busyId === a.user ? "Approving…" : "Approve"}
                  </button>
                ) : (
                  <span className="text-xs text-foreground/40">Approved</span>
                ),
            },
          ]}
        />
      </Panel>
    </div>
  );
}
