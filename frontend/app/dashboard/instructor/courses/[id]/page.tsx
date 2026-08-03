"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ArrowLeft } from "lucide-react";
import { DataTable } from "@/components/dashboard/DataTable";
import { ErrorState, LoadingState } from "@/components/dashboard/DashboardStates";
import { Panel } from "@/components/dashboard/Panel";
import { AssignmentsBuilder } from "@/components/dashboard/course-builder/AssignmentsBuilder";
import { CodingExerciseBuilder } from "@/components/dashboard/course-builder/CodingExerciseBuilder";
import { CourseCoverImage } from "@/components/dashboard/course-builder/CourseCoverImage";
import { LiveSessionsBuilder } from "@/components/dashboard/course-builder/LiveSessionsBuilder";
import { QuizBuilder } from "@/components/dashboard/course-builder/QuizBuilder";
import { SectionsBuilder } from "@/components/dashboard/course-builder/SectionsBuilder";
import { ApiError } from "@/lib/api/client";
import { listSections } from "@/lib/api/content";
import {
  createCourseCoupon,
  getInstructorCourse,
  publishCourse,
  submitCourseForReview,
} from "@/lib/api/instructorCourses";
import type { Coupon, CourseWriteResult, Section } from "@/lib/api/types";
import { useAuth } from "@/lib/auth/AuthContext";

const STATUS_STYLES: Record<string, string> = {
  draft: "bg-foreground/10 text-foreground/70",
  submitted: "bg-amber-500/10 text-amber-400",
  approved: "bg-teal-400/10 text-teal-400",
  rejected: "bg-rose-500/10 text-rose-400",
  published: "bg-emerald-500/10 text-emerald-400",
  archived: "bg-foreground/10 text-foreground/50",
};

function CourseCouponsBuilder({
  courseId,
  token,
}: {
  courseId: string;
  token: string;
}) {
  const [coupons, setCoupons] = useState<Coupon[]>([]);
  const [code, setCode] = useState("");
  const [discountType, setDiscountType] = useState<"percent" | "fixed">("percent");
  const [discountValue, setDiscountValue] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!code || !discountValue) return;
    setSaving(true);
    setError(null);
    try {
      const coupon = await createCourseCoupon(
        courseId,
        { code, discount_type: discountType, discount_value: discountValue },
        token
      );
      setCoupons((prev) => [coupon, ...prev]);
      setCode("");
      setDiscountValue("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't create this coupon.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-3">
      <form
        onSubmit={handleSubmit}
        className="flex flex-wrap items-end gap-2 rounded-xl border border-border bg-surface p-4"
      >
        <div>
          <label className="block text-xs font-medium text-foreground/60">Code</label>
          <input
            type="text"
            value={code}
            onChange={(e) => setCode(e.target.value.toUpperCase())}
            className="mt-1 w-32 rounded-lg border border-border-strong bg-surface px-2 py-1.5 text-sm text-foreground focus:border-teal-400 focus:outline-none"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-foreground/60">Type</label>
          <select
            value={discountType}
            onChange={(e) => setDiscountType(e.target.value as "percent" | "fixed")}
            className="mt-1 rounded-lg border border-border-strong bg-surface px-2 py-1.5 text-sm text-foreground focus:border-teal-400 focus:outline-none"
          >
            <option value="percent">Percent</option>
            <option value="fixed">Fixed amount</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-foreground/60">Value</label>
          <input
            type="number"
            value={discountValue}
            onChange={(e) => setDiscountValue(e.target.value)}
            className="mt-1 w-24 rounded-lg border border-border-strong bg-surface px-2 py-1.5 text-sm text-foreground focus:border-teal-400 focus:outline-none"
          />
        </div>
        <button
          type="submit"
          disabled={saving || !code || !discountValue}
          className="rounded-full bg-teal-400 px-4 py-1.5 text-sm font-semibold text-emerald-950 transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {saving ? "Creating…" : "Create coupon"}
        </button>
        {error && <p className="w-full text-xs text-rose-400">{error}</p>}
      </form>
      <DataTable
        rows={coupons}
        getRowKey={(c) => c.id}
        emptyMessage="No coupons created yet for this course."
        columns={[
          { header: "Code", cell: (c) => c.code },
          {
            header: "Discount",
            cell: (c) =>
              c.discount_type === "percent" ? `${c.discount_value}%` : `$${c.discount_value}`,
          },
          { header: "Usage limit", cell: (c) => c.usage_limit ?? "Unlimited" },
        ]}
      />
    </div>
  );
}

export default function CourseBuilderPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { accessToken } = useAuth();

  const [course, setCourse] = useState<CourseWriteResult | null>(null);
  const [sections, setSections] = useState<Section[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [lifecycleBusy, setLifecycleBusy] = useState(false);

  useEffect(() => {
    if (!accessToken) return;
    let cancelled = false;

    Promise.all([getInstructorCourse(id, accessToken), listSections(id, accessToken)])
      .then(([courseData, sectionsData]) => {
        if (cancelled) return;
        setCourse(courseData);
        setSections(sectionsData);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message_ : "Couldn't load this course.");
        }
      });

    return () => {
      cancelled = true;
    };
  }, [id, accessToken]);

  async function handleSubmitForReview() {
    if (!accessToken || !course) return;
    setLifecycleBusy(true);
    try {
      const updated = await submitCourseForReview(course.id, accessToken);
      setCourse((prev) => (prev ? { ...prev, status: updated.status } : prev));
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't submit this course for review.");
    } finally {
      setLifecycleBusy(false);
    }
  }

  async function handlePublish() {
    if (!accessToken || !course) return;
    setLifecycleBusy(true);
    try {
      const updated = await publishCourse(course.id, accessToken);
      setCourse((prev) => (prev ? { ...prev, status: updated.status } : prev));
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't publish this course.");
    } finally {
      setLifecycleBusy(false);
    }
  }

  if (error && !course) return <ErrorState message={error} />;
  if (!course) return <LoadingState label="Loading course…" />;

  return (
    <div className="space-y-10">
      <div>
        <button
          type="button"
          onClick={() => router.push("/dashboard/instructor")}
          className="flex items-center gap-1.5 text-sm text-foreground/50 hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" /> Back to dashboard
        </button>

        <div className="mt-4 flex flex-wrap items-start justify-between gap-4">
          <div className="flex flex-wrap items-start gap-4">
            <CourseCoverImage
              courseId={course.id}
              coverImage={course.cover_image}
              token={accessToken!}
              onUploaded={(coverImage) =>
                setCourse((prev) => (prev ? { ...prev, cover_image: coverImage } : prev))
              }
            />
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-semibold text-foreground">{course.title}</h1>
                <span
                  className={`rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${
                    STATUS_STYLES[course.status] ?? ""
                  }`}
                >
                  {course.status}
                </span>
              </div>
              {course.summary && (
                <p className="mt-1 text-sm text-foreground/60">{course.summary}</p>
              )}
            </div>
          </div>

          <div className="flex gap-2">
            {(course.status === "draft" || course.status === "rejected") && (
              <button
                type="button"
                onClick={handleSubmitForReview}
                disabled={lifecycleBusy}
                className="rounded-full border border-border-strong px-4 py-2 text-sm font-semibold text-foreground/80 transition-colors hover:bg-surface-hover disabled:opacity-50"
              >
                Submit for review
              </button>
            )}
            {course.status === "approved" && (
              <button
                type="button"
                onClick={handlePublish}
                disabled={lifecycleBusy}
                className="rounded-full bg-teal-400 px-4 py-2 text-sm font-semibold text-emerald-950 transition-opacity hover:opacity-90 disabled:opacity-50"
              >
                Publish
              </button>
            )}
          </div>
        </div>

        {error && <p className="mt-3 text-sm text-rose-400">{error}</p>}
      </div>

      <Panel
        title="Curriculum"
        subtitle="Organize your course into sections, then add lessons to each one."
      >
        <SectionsBuilder
          courseId={course.id}
          token={accessToken!}
          sections={sections}
          onSectionCreated={(section) => setSections((prev) => [...prev, section])}
        />
      </Panel>

      <Panel
        title="Quizzes"
        subtitle="Build a quiz with multiple-choice questions, optionally tied to a section."
      >
        <QuizBuilder courseId={course.id} sections={sections} token={accessToken!} />
      </Panel>

      <Panel title="Assignments" subtitle="Written or project-based work students submit for grading.">
        <AssignmentsBuilder courseId={course.id} token={accessToken!} />
      </Panel>

      <Panel title="Coding exercises" subtitle="Auto-graded Python exercises with test cases.">
        <CodingExerciseBuilder courseId={course.id} sections={sections} token={accessToken!} />
      </Panel>

      <Panel
        title="Live sessions"
        subtitle="Schedule Zoom or Google Meet sessions for students enrolled in this course."
      >
        <LiveSessionsBuilder courseId={course.id} token={accessToken!} />
      </Panel>

      <Panel
        title="Coupons"
        subtitle="Create discount codes scoped to this course. Only coupons created in this session are listed below."
      >
        <CourseCouponsBuilder courseId={course.id} token={accessToken!} />
      </Panel>

      <p className="text-xs text-foreground/40">
        Slug: {course.slug} ·{" "}
        <Link href={`/courses/${course.id}`} className="underline hover:text-foreground/60">
          View public page
        </Link>
      </p>
    </div>
  );
}
