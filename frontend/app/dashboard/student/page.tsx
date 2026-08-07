"use client";

import { Award, BookOpen, Download, Heart, PlayCircle, Radio } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { ErrorState, LoadingState } from "@/components/dashboard/DashboardStates";
import { DataTable } from "@/components/dashboard/DataTable";
import { LiveSessionJoinAction } from "@/components/dashboard/LiveSessionJoinAction";
import { PageHeader } from "@/components/dashboard/PageHeader";
import { Panel } from "@/components/dashboard/Panel";
import { StatCard } from "@/components/dashboard/StatCard";
import { ApiError } from "@/lib/api/client";
import {
  listCertificates,
  listContinueLearning,
  listMyCourses,
  listMyGrades,
  listWishlist,
} from "@/lib/api/enrollments";
import { listMyLiveSessions } from "@/lib/api/liveSessions";
import type { Certificate, Enrollment, GradeEntry, LiveSession, WishlistItem } from "@/lib/api/types";
import { useAuth } from "@/lib/auth/AuthContext";
import { Reveal } from "@/components/animation/Reveal";

interface StudentData {
  continueLearning: Enrollment[];
  myCourses: Enrollment[];
  wishlist: WishlistItem[];
  grades: GradeEntry[];
  certificates: Certificate[];
  liveSessions: LiveSession[];
}

export default function StudentDashboardPage() {
  const { accessToken } = useAuth();
  const [data, setData] = useState<StudentData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken) return;
    let cancelled = false;

    Promise.all([
      listContinueLearning(accessToken),
      listMyCourses(accessToken),
      listWishlist(accessToken),
      listMyGrades(accessToken),
      listCertificates(accessToken),
      listMyLiveSessions(accessToken),
    ])
      .then(([continueLearning, myCourses, wishlist, grades, certificates, liveSessions]) => {
        if (cancelled) return;
        setData({
          continueLearning,
          myCourses: myCourses.results,
          wishlist,
          grades,
          certificates: certificates.results,
          liveSessions,
        });
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err instanceof ApiError ? err.message_ : "Couldn't load your dashboard.");
      });

    return () => {
      cancelled = true;
    };
  }, [accessToken]);

  if (error) return <ErrorState message={error} />;
  if (!data) return <LoadingState label="Loading your learning dashboard…" />;

  const completedCount = data.myCourses.filter((e) => e.status === "completed").length;

  return (
    <div className="space-y-8">
      <PageHeader title="My learning" />

      <Reveal className="grid grid-cols-2 gap-4 sm:grid-cols-4" stagger={0.08}>
        <StatCard label="Enrolled" value={String(data.myCourses.length)} icon={BookOpen} />
        <StatCard label="Completed" value={String(completedCount)} icon={Award} />
        <StatCard label="Wishlist" value={String(data.wishlist.length)} icon={Heart} />
        <StatCard
          label="Upcoming live sessions"
          value={String(
            data.liveSessions.filter((s) => s.status === "scheduled" || s.status === "live").length
          )}
          icon={Radio}
        />
      </Reveal>

      <Panel title="Continue learning">
        {data.continueLearning.length === 0 ? (
          <p className="text-sm text-foreground/50">
            Nothing in progress yet.{" "}
            <Link href="/courses" className="text-teal-400 hover:underline">
              Browse courses
            </Link>{" "}
            to get started.
          </p>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {data.continueLearning.map((enrollment) => (
              <Link
                key={enrollment.id}
                href={`/learn/${enrollment.course.id}`}
                className="group flex items-center gap-3 rounded-xl border border-border bg-background/40 p-4 transition-colors hover:border-teal-400/50 hover:bg-surface-hover"
              >
                <PlayCircle className="h-8 w-8 flex-none text-teal-400" />
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold text-foreground group-hover:text-teal-600 dark:group-hover:text-teal-300">
                    {enrollment.course.title}
                  </p>
                  <p className="text-xs text-foreground/50">{enrollment.status}</p>
                </div>
              </Link>
            ))}
          </div>
        )}
      </Panel>

      <Panel title="Live sessions">
        <DataTable
          rows={data.liveSessions}
          getRowKey={(s) => s.id}
          emptyMessage="You haven't registered for any live sessions yet."
          columns={[
            { header: "Session", cell: (s) => s.title },
            {
              header: "Starts",
              cell: (s) => new Date(s.scheduled_start_at).toLocaleString(),
            },
            { header: "Status", cell: (s) => <span className="capitalize">{s.status}</span> },
            { header: "", cell: (s) => <LiveSessionJoinAction session={s} /> },
          ]}
        />
      </Panel>

      <Panel title="My courses">
        <DataTable
          rows={data.myCourses}
          getRowKey={(e) => e.id}
          emptyMessage="You haven't enrolled in any courses yet."
          columns={[
            { header: "Course", cell: (e) => e.course.title },
            {
              header: "Status",
              cell: (e) => (
                <span className="capitalize text-foreground/70">{e.status}</span>
              ),
            },
            { header: "Enrolled", cell: (e) => new Date(e.enrolled_at).toLocaleDateString() },
            {
              header: "",
              cell: (e) => (
                <Link href={`/learn/${e.course.id}`} className="text-teal-400 hover:underline">
                  Continue
                </Link>
              ),
            },
          ]}
        />
      </Panel>

      <Panel title="Grades">
        <DataTable
          rows={data.grades}
          getRowKey={(g) => `${g.type}-${g.id}`}
          emptyMessage="No graded quizzes or assignments yet."
          columns={[
            { header: "Title", cell: (g) => g.title },
            { header: "Type", cell: (g) => <span className="capitalize">{g.type}</span> },
            {
              header: "Score",
              cell: (g) =>
                g.type === "quiz"
                  ? g.score !== null
                    ? `${g.score}%`
                    : "—"
                  : g.grade !== null
                    ? `${g.grade}%`
                    : "—",
            },
            {
              header: "Result",
              cell: (g) =>
                g.type === "quiz" ? (
                  g.passed === null ? (
                    "—"
                  ) : (
                    <span className={g.passed ? "text-emerald-400" : "text-rose-400"}>
                      {g.passed ? "Passed" : "Failed"}
                    </span>
                  )
                ) : (
                  "Graded"
                ),
            },
          ]}
        />
      </Panel>

      <Panel title="Certificates">
        <DataTable
          rows={data.certificates}
          getRowKey={(c) => c.id}
          emptyMessage="Complete a course to earn your first certificate."
          columns={[
            { header: "Course", cell: (c) => c.course.title },
            { header: "Certificate ID", cell: (c) => c.certificate_uid },
            { header: "Issued", cell: (c) => new Date(c.issued_at).toLocaleDateString() },
            {
              header: "",
              cell: (c) =>
                c.pdf_file ? (
                  <a
                    href={c.pdf_file}
                    download
                    className="flex items-center gap-1 text-teal-400 hover:underline"
                  >
                    <Download className="h-3.5 w-3.5" /> Download
                  </a>
                ) : (
                  <span className="text-foreground/30">Preparing…</span>
                ),
            },
          ]}
        />
      </Panel>

      <Panel title="Wishlist">
        <DataTable
          rows={data.wishlist}
          getRowKey={(w) => w.course.id}
          emptyMessage="Nothing wishlisted yet."
          columns={[
            { header: "Course", cell: (w) => w.course.title },
            { header: "Added", cell: (w) => new Date(w.added_at).toLocaleDateString() },
            {
              header: "",
              cell: (w) => (
                <Link href={`/courses/${w.course.id}`} className="text-teal-400 hover:underline">
                  View
                </Link>
              ),
            },
          ]}
        />
      </Panel>
    </div>
  );
}
