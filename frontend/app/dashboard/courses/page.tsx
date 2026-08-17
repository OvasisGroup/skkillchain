"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import { DataTable } from "@/components/dashboard/DataTable";
import { ErrorState, LoadingState } from "@/components/dashboard/DashboardStates";
import { PageHeader } from "@/components/dashboard/PageHeader";
import { deleteAdminCourse, listAdminCourses } from "@/lib/api/adminCourses";
import { ApiError } from "@/lib/api/client";
import type { Course } from "@/lib/api/types";
import { useAuth } from "@/lib/auth/AuthContext";

const STATUS_STYLES: Record<string, string> = {
  draft: "bg-foreground/10 text-foreground/70",
  submitted: "bg-amber-500/10 text-amber-400",
  approved: "bg-teal-400/10 text-teal-400",
  rejected: "bg-rose-500/10 text-rose-400",
  published: "bg-emerald-500/10 text-emerald-400",
  archived: "bg-foreground/10 text-foreground/50",
};

const STATUS_FILTERS = ["all", "draft", "submitted", "approved", "rejected", "published", "archived"];

export default function AdminCoursesPage() {
  const { accessToken } = useAuth();
  const [courses, setCourses] = useState<Course[] | null>(null);
  const [status, setStatus] = useState("all");
  const [q, setQ] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken) return;
    let cancelled = false;
    listAdminCourses(accessToken, { status: status === "all" ? undefined : status, q: q || undefined })
      .then((page) => {
        if (!cancelled) setCourses(page.results);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message_ : "Couldn't load courses.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [accessToken, status, q]);

  async function handleDelete(course: Course) {
    if (!accessToken) return;
    if (!window.confirm(`Delete "${course.title}"? This permanently removes its curriculum and cannot be undone.`)) {
      return;
    }
    setDeletingId(course.id);
    setDeleteError(null);
    try {
      await deleteAdminCourse(course.id, accessToken);
      setCourses((prev) => prev?.filter((c) => c.id !== course.id) ?? prev);
    } catch (err) {
      setDeleteError(err instanceof ApiError ? err.message_ : "Couldn't delete this course.");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Admin"
        title="Courses"
        subtitle="Every course on the platform, regardless of owner or status."
        actions={
          <Link
            href="/dashboard/courses/new"
            className="flex items-center gap-1.5 rounded-full bg-teal-400 px-4 py-2 text-sm font-semibold text-emerald-950 transition-opacity hover:opacity-90"
          >
            <Plus className="h-4 w-4" />
            Create for instructor
          </Link>
        }
      />

      <div className="flex flex-wrap items-center gap-2">
        {STATUS_FILTERS.map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => setStatus(s)}
            className={`rounded-full border px-3 py-1.5 text-xs font-medium capitalize transition-colors ${
              status === s
                ? "border-teal-400 bg-teal-400/10 text-teal-400"
                : "border-border-strong text-foreground/60 hover:bg-surface-hover"
            }`}
          >
            {s}
          </button>
        ))}
        <input
          type="search"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search title or summary…"
          className="ml-auto w-56 rounded-full border border-border-strong bg-surface px-3.5 py-1.5 text-sm text-foreground focus:border-teal-400 focus:outline-none"
        />
      </div>

      {error && <ErrorState message={error} />}
      {deleteError && <div className="rounded-lg bg-red-500/10 p-3 text-sm text-red-400">{deleteError}</div>}
      {!error && !courses && <LoadingState label="Loading courses…" />}
      {!error && courses && (
        <DataTable
          rows={courses}
          getRowKey={(c) => c.id}
          emptyMessage="No courses match these filters."
          columns={[
            {
              header: "Title",
              cell: (c) => (
                <Link href={`/dashboard/courses/${c.id}`} className="font-medium text-foreground hover:text-teal-400">
                  {c.title}
                </Link>
              ),
            },
            { header: "Instructor", cell: (c) => c.instructor.email },
            {
              header: "Status",
              cell: (c) => (
                <span
                  className={`rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${STATUS_STYLES[c.status] ?? ""}`}
                >
                  {c.status}
                </span>
              ),
            },
            {
              header: "Price",
              cell: (c) => (c.price_amount === "0.00" ? "Free" : `${c.currency} ${c.price_amount}`),
            },
            {
              header: "Published",
              cell: (c) => (c.published_at ? new Date(c.published_at).toLocaleDateString() : "—"),
            },
            {
              header: "",
              cell: (c) => (
                <button
                  type="button"
                  onClick={() => handleDelete(c)}
                  disabled={deletingId === c.id}
                  aria-label={`Delete ${c.title}`}
                  className="rounded-full p-1.5 text-foreground/40 transition-colors hover:bg-rose-500 hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              ),
              className: "text-right",
            },
          ]}
        />
      )}
    </div>
  );
}
