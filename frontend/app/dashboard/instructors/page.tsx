"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { DataTable } from "@/components/dashboard/DataTable";
import { ErrorState, LoadingState } from "@/components/dashboard/DashboardStates";
import { PageHeader } from "@/components/dashboard/PageHeader";
import { listUsers } from "@/lib/api/admin";
import { ApiError } from "@/lib/api/client";
import type { AdminUser } from "@/lib/api/types";
import { useAuth } from "@/lib/auth/AuthContext";

export default function AdminInstructorsPage() {
  const { accessToken } = useAuth();
  const [instructors, setInstructors] = useState<AdminUser[] | null>(null);
  const [q, setQ] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken) return;
    let cancelled = false;
    listUsers(accessToken, { role: "instructor", email: q || undefined })
      .then((page) => {
        if (!cancelled) setInstructors(page.results);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message_ : "Couldn't load instructors.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [accessToken, q]);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Admin"
        title="Instructors"
        subtitle="Maintain instructor details — profile photo, bio, and contact links — on their behalf."
      />

      <input
        type="search"
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder="Search by name or email…"
        className="w-64 rounded-full border border-border-strong bg-surface px-3.5 py-1.5 text-sm text-foreground focus:border-teal-400 focus:outline-none"
      />

      {error && <ErrorState message={error} />}
      {!error && !instructors && <LoadingState label="Loading instructors…" />}
      {!error && instructors && (
        <DataTable
          rows={instructors}
          getRowKey={(u) => u.id}
          emptyMessage="No instructors match this search."
          columns={[
            {
              header: "",
              cell: (u) => (
                <div className="flex h-9 w-9 items-center justify-center overflow-hidden rounded-full border border-border-strong bg-surface-hover">
                  {u.profile.avatar ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={u.profile.avatar} alt="" className="h-full w-full object-cover" />
                  ) : (
                    <span className="text-[10px] text-foreground/30">—</span>
                  )}
                </div>
              ),
              className: "w-9",
            },
            {
              header: "Name",
              cell: (u) => (
                <Link
                  href={`/dashboard/instructors/${u.id}?email=${encodeURIComponent(u.email)}`}
                  className="font-medium text-foreground hover:text-teal-400"
                >
                  {[u.profile.first_name, u.profile.last_name].filter(Boolean).join(" ") || "—"}
                </Link>
              ),
            },
            { header: "Email", cell: (u) => u.email },
            {
              header: "Bio",
              cell: (u) => (
                <span className="line-clamp-1 max-w-xs text-foreground/60">
                  {u.profile.bio || "—"}
                </span>
              ),
            },
            {
              header: "Status",
              cell: (u) => (
                <span
                  className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                    u.is_active ? "bg-emerald-500/10 text-emerald-400" : "bg-rose-500/10 text-rose-400"
                  }`}
                >
                  {u.is_active ? "Active" : "Suspended"}
                </span>
              ),
            },
          ]}
        />
      )}
    </div>
  );
}
