"use client";

import { BadgeCheck, BookOpen, ClipboardCheck, DollarSign, GraduationCap, Plus, Video, Wallet as WalletIcon } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { DataTable } from "@/components/dashboard/DataTable";
import { ErrorState, LoadingState } from "@/components/dashboard/DashboardStates";
import { GradeSubmissionRow } from "@/components/dashboard/GradeSubmissionRow";
import { PageHeader } from "@/components/dashboard/PageHeader";
import { Panel } from "@/components/dashboard/Panel";
import { StatCard } from "@/components/dashboard/StatCard";
import { ApiError } from "@/lib/api/client";
import { listCourseAssignments, listAssignmentSubmissions } from "@/lib/api/grading";
import { applyAsInstructor } from "@/lib/api/moderation";
import { listInstructorCourses, publishCourse, submitCourseForReview } from "@/lib/api/instructorCourses";
import { getInstructorEarnings, getInstructorWallet, listInstructorPayouts, requestInstructorPayout } from "@/lib/api/payouts";
import type { Assignment, AssignmentSubmission, Course, EarningsAggregate, Payout, Wallet } from "@/lib/api/types";
import { useAuth } from "@/lib/auth/AuthContext";
import { hasRole } from "@/lib/auth/roles";
import { Reveal } from "@/components/animation/Reveal";

interface PendingSubmission {
  assignment: Assignment;
  submission: AssignmentSubmission;
}

const STATUS_STYLES: Record<string, string> = {
  draft: "bg-foreground/10 text-foreground/70",
  submitted: "bg-amber-500/10 text-amber-400",
  approved: "bg-teal-400/10 text-teal-400",
  rejected: "bg-rose-500/10 text-rose-400",
  published: "bg-emerald-500/10 text-emerald-400",
  archived: "bg-foreground/10 text-foreground/50",
};

export default function InstructorDashboardPage() {
  const { accessToken, user } = useAuth();
  const isInstructor = hasRole(user, "instructor");
  const [courses, setCourses] = useState<Course[] | null>(null);
  const [wallet, setWallet] = useState<Wallet | null>(null);
  const [payouts, setPayouts] = useState<Payout[]>([]);
  const [earnings, setEarnings] = useState<EarningsAggregate[]>([]);
  const [pending, setPending] = useState<PendingSubmission[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busyCourseId, setBusyCourseId] = useState<string | null>(null);
  const [payoutBusy, setPayoutBusy] = useState(false);
  const [applying, setApplying] = useState(false);
  const [applied, setApplied] = useState(false);
  const [applyError, setApplyError] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken || !isInstructor) return;
    let cancelled = false;

    async function load() {
      const token = accessToken as string;
      const [coursesPage, walletData, payoutsData, earningsData] = await Promise.all([
        listInstructorCourses(token),
        getInstructorWallet(token),
        listInstructorPayouts(token),
        getInstructorEarnings(token),
      ]);
      if (cancelled) return;
      setCourses(coursesPage.results);
      setWallet(walletData);
      setPayouts(payoutsData);
      setEarnings(earningsData);

      const perCourseAssignments = await Promise.all(
        coursesPage.results.map((course) => listCourseAssignments(course.id, token))
      );
      const assignments = perCourseAssignments.flat();

      const perAssignmentSubmissions = await Promise.all(
        assignments.map((assignment) => listAssignmentSubmissions(assignment.id, token))
      );
      if (cancelled) return;

      const stillPending: PendingSubmission[] = [];
      assignments.forEach((assignment, index) => {
        perAssignmentSubmissions[index]
          .filter((submission) => submission.grade === null)
          .forEach((submission) => stillPending.push({ assignment, submission }));
      });
      setPending(stillPending);
    }

    load().catch((err) => {
      if (cancelled) return;
      setError(err instanceof ApiError ? err.message_ : "Couldn't load your instructor dashboard.");
    });

    return () => {
      cancelled = true;
    };
  }, [accessToken, isInstructor]);

  async function handleApply() {
    if (!accessToken) return;
    setApplying(true);
    setApplyError(null);
    try {
      await applyAsInstructor(accessToken);
      setApplied(true);
    } catch (err) {
      setApplyError(err instanceof ApiError ? err.message_ : "Couldn't submit your application.");
    } finally {
      setApplying(false);
    }
  }

  async function handleSubmitForReview(courseId: string) {
    if (!accessToken) return;
    setBusyCourseId(courseId);
    try {
      const updated = await submitCourseForReview(courseId, accessToken);
      setCourses((prev) =>
        prev?.map((c) => (c.id === courseId ? { ...c, status: updated.status } : c)) ?? prev
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't submit this course for review.");
    } finally {
      setBusyCourseId(null);
    }
  }

  async function handlePublish(courseId: string) {
    if (!accessToken) return;
    setBusyCourseId(courseId);
    try {
      const updated = await publishCourse(courseId, accessToken);
      setCourses((prev) =>
        prev?.map((c) => (c.id === courseId ? { ...c, status: updated.status } : c)) ?? prev
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't publish this course.");
    } finally {
      setBusyCourseId(null);
    }
  }

  async function handleRequestPayout() {
    if (!accessToken) return;
    setPayoutBusy(true);
    try {
      const payout = await requestInstructorPayout(accessToken);
      setPayouts((prev) => [payout, ...prev]);
      setWallet((prev) => (prev ? { ...prev, balance_amount: "0.00" } : prev));
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't request a payout.");
    } finally {
      setPayoutBusy(false);
    }
  }

  function handleGraded(submissionId: string) {
    setPending((prev) => prev.filter((p) => p.submission.id !== submissionId));
  }

  if (!isInstructor) {
    return (
      <div className="rounded-2xl border border-border bg-surface p-8 text-center">
        <GraduationCap className="mx-auto h-8 w-8 text-teal-400" />
        <h1 className="mt-4 text-xl font-semibold text-foreground">Become an instructor</h1>
        <p className="mt-2 text-sm text-foreground/60">
          Apply to teach on SkillChain and start publishing your own courses.
        </p>
        {applied ? (
          <p className="mt-6 text-sm text-emerald-400">
            Application submitted — we&apos;ll email you once it&apos;s approved.
          </p>
        ) : (
          <button
            type="button"
            onClick={handleApply}
            disabled={applying}
            className="mt-6 rounded-full bg-teal-400 px-6 py-2.5 text-sm font-semibold text-emerald-950 transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {applying ? "Submitting…" : "Apply to teach"}
          </button>
        )}
        {applyError && <p className="mt-4 text-sm text-rose-400">{applyError}</p>}
      </div>
    );
  }

  if (error) return <ErrorState message={error} />;
  if (!courses) return <LoadingState label="Loading your instructor dashboard…" />;

  const publishedCount = courses.filter((c) => c.status === "published").length;

  return (
    <div className="space-y-8">
      <PageHeader
        title="Instructor"
        actions={
          <Link
            href="/dashboard/instructor/conferencing-accounts"
            className="flex items-center gap-1.5 rounded-full border border-border-strong px-4 py-1.5 text-sm font-semibold text-foreground/80 transition-colors hover:bg-surface-hover"
          >
            <Video className="h-4 w-4" /> Conferencing accounts
          </Link>
        }
      />

      <Reveal className="grid grid-cols-2 gap-4 sm:grid-cols-4" stagger={0.08}>
        <StatCard label="Courses" value={String(courses.length)} icon={BookOpen} />
        <StatCard label="Published" value={String(publishedCount)} icon={BadgeCheck} />
        <StatCard
          label="Wallet balance"
          value={wallet ? `${wallet.currency} ${wallet.balance_amount}` : "—"}
          icon={WalletIcon}
        />
        <StatCard label="Needs grading" value={String(pending.length)} icon={ClipboardCheck} />
      </Reveal>

      <Panel
        title="My courses"
        actions={
          <Link
            href="/dashboard/instructor/courses/new"
            className="flex items-center gap-1.5 rounded-full bg-teal-400 px-4 py-1.5 text-sm font-semibold text-emerald-950 transition-opacity hover:opacity-90"
          >
            <Plus className="h-4 w-4" /> New course
          </Link>
        }
      >
        <DataTable
          rows={courses}
          getRowKey={(c) => c.id}
          emptyMessage="You haven't created any courses yet."
          columns={[
            {
              header: "Title",
              cell: (c) => (
                <Link
                  href={`/dashboard/instructor/courses/${c.id}`}
                  className="font-medium text-foreground hover:text-teal-400"
                >
                  {c.title}
                </Link>
              ),
            },
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
            { header: "Price", cell: (c) => `${c.currency} ${c.price_amount}` },
            {
              header: "",
              cell: (c) => (
                <div className="flex gap-2">
                  <Link
                    href={`/dashboard/instructor/courses/${c.id}`}
                    className="rounded-full border border-border-strong px-3 py-1 text-xs font-semibold text-foreground/80 transition-colors hover:bg-surface-hover"
                  >
                    Manage
                  </Link>
                  {(c.status === "draft" || c.status === "rejected") && (
                    <button
                      type="button"
                      onClick={() => handleSubmitForReview(c.id)}
                      disabled={busyCourseId === c.id}
                      className="rounded-full border border-border-strong px-3 py-1 text-xs font-semibold text-foreground/80 transition-colors hover:bg-surface-hover disabled:opacity-50"
                    >
                      Submit for review
                    </button>
                  )}
                  {c.status === "approved" && (
                    <button
                      type="button"
                      onClick={() => handlePublish(c.id)}
                      disabled={busyCourseId === c.id}
                      className="rounded-full bg-teal-400 px-3 py-1 text-xs font-semibold text-emerald-950 transition-opacity hover:opacity-90 disabled:opacity-50"
                    >
                      Publish
                    </button>
                  )}
                </div>
              ),
            },
          ]}
        />
      </Panel>

      <Panel title="Wallet & payouts">
        <div className="flex flex-wrap items-center gap-4 rounded-xl border border-border bg-background/40 p-4">
          <div className="flex items-center gap-2 text-sm text-foreground/70">
            <DollarSign className="h-4 w-4 text-teal-400" />
            Available balance: <span className="font-semibold text-foreground">{wallet ? `${wallet.currency} ${wallet.balance_amount}` : "—"}</span>
          </div>
          <button
            type="button"
            onClick={handleRequestPayout}
            disabled={payoutBusy || !wallet || Number(wallet.balance_amount) <= 0}
            className="rounded-full bg-teal-400 px-4 py-1.5 text-sm font-semibold text-emerald-950 transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {payoutBusy ? "Requesting…" : "Request payout"}
          </button>
        </div>
        <div className="mt-4">
          <DataTable
            rows={payouts}
            getRowKey={(p) => p.id}
            emptyMessage="No payouts requested yet."
            columns={[
              { header: "Period", cell: (p) => `${p.period_start} – ${p.period_end}` },
              { header: "Gross", cell: (p) => p.amount_gross },
              { header: "Net", cell: (p) => p.amount_net },
              { header: "Status", cell: (p) => <span className="capitalize">{p.status}</span> },
            ]}
          />
        </div>
      </Panel>

      <Panel title="Earnings">
        <DataTable
          rows={earnings}
          getRowKey={(e) => `${e.period_start}-${e.period_end}`}
          emptyMessage="No earnings recorded yet."
          columns={[
            { header: "Period", cell: (e) => `${e.period_start} – ${e.period_end}` },
            { header: "Gross", cell: (e) => `${e.currency} ${e.gross_amount}` },
            { header: "Net", cell: (e) => `${e.currency} ${e.net_amount}` },
          ]}
        />
      </Panel>

      <Panel title="Assignments to grade">
        {pending.length === 0 ? (
          <p className="text-sm text-foreground/50">Nothing waiting on you — all caught up.</p>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-border">
            <table className="w-full min-w-[720px] text-left text-sm">
              <thead>
                <tr className="border-b border-border bg-surface-hover/60">
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-foreground/50">Assignment</th>
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-foreground/50">Student</th>
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-foreground/50">Submission</th>
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-foreground/50">Grade</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {pending.map(({ assignment, submission }) => (
                  <GradeSubmissionRow
                    key={submission.id}
                    assignmentId={assignment.id}
                    assignmentTitle={assignment.title}
                    submission={submission}
                    onGraded={handleGraded}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>
    </div>
  );
}
