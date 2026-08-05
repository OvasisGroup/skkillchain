"use client";

import { useEffect, useState } from "react";
import { DataTable } from "@/components/dashboard/DataTable";
import { ApiError } from "@/lib/api/client";
import { listCourseStudents } from "@/lib/api/instructorCourses";
import type { CourseStudentProgress } from "@/lib/api/types";

const STATUS_STYLES: Record<string, string> = {
  active: "bg-teal-400/10 text-teal-400",
  completed: "bg-emerald-500/10 text-emerald-400",
};

function studentName(student: CourseStudentProgress["student"]): string {
  const name = `${student.profile.first_name} ${student.profile.last_name}`.trim();
  return name || student.email;
}

function ProgressBar({ percent }: { percent: number }) {
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-24 overflow-hidden rounded-full bg-surface-hover">
        <div
          className="h-full rounded-full bg-teal-400"
          style={{ width: `${Math.min(percent, 100)}%` }}
        />
      </div>
      <span className="text-xs text-foreground/60">{percent}%</span>
    </div>
  );
}

export function StudentsPanel({ courseId, token }: { courseId: string; token: string }) {
  const [students, setStudents] = useState<CourseStudentProgress[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    listCourseStudents(courseId, token)
      .then((data) => {
        if (!cancelled) setStudents(data);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message_ : "Couldn't load enrolled students.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [courseId, token]);

  if (error) return <p className="text-sm text-rose-400">{error}</p>;
  if (!students) return <p className="text-sm text-foreground/50">Loading students…</p>;

  return (
    <DataTable
      rows={students}
      getRowKey={(row) => row.enrollment_id}
      emptyMessage="No students enrolled yet."
      columns={[
        { header: "Student", cell: (row) => studentName(row.student) },
        { header: "Email", cell: (row) => row.student.email },
        {
          header: "Status",
          cell: (row) => (
            <span
              className={`rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${
                STATUS_STYLES[row.status] ?? ""
              }`}
            >
              {row.status}
            </span>
          ),
        },
        { header: "Progress", cell: (row) => <ProgressBar percent={row.overall_percent} /> },
        {
          header: "Enrolled",
          cell: (row) => new Date(row.enrolled_at).toLocaleDateString(),
        },
      ]}
    />
  );
}
