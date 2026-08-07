"use client";

import { useEffect, useState } from "react";
import { authInputClass } from "@/components/AuthCard";
import { ApiError } from "@/lib/api/client";
import { createAssignment } from "@/lib/api/assessments";
import { listCourseAssignments } from "@/lib/api/grading";
import type { Assignment } from "@/lib/api/types";

export function AssignmentsBuilder({ courseId, token }: { courseId: string; token: string }) {
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [title, setTitle] = useState("");
  const [instructions, setInstructions] = useState("");
  const [dueAt, setDueAt] = useState("");
  const [allowLate, setAllowLate] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    listCourseAssignments(courseId, token)
      .then((data) => {
        if (!cancelled) setAssignments(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof ApiError ? err.message_ : "Couldn't load assignments.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [courseId, token]);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!title.trim() || !instructions.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      const duePolicy: Record<string, unknown> = { allow_late: allowLate };
      if (dueAt) duePolicy.due_at = new Date(dueAt).toISOString();
      const assignment = await createAssignment(
        courseId,
        { title, instructions, due_policy: duePolicy },
        token
      );
      setAssignments((prev) => [...prev, assignment]);
      setTitle("");
      setInstructions("");
      setDueAt("");
      setAllowLate(false);
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't create the assignment.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-4">
      {loading ? (
        <p className="text-sm text-foreground/50">Loading assignments…</p>
      ) : (
        assignments.length > 0 && (
          <ul className="space-y-2">
            {assignments.map((assignment) => (
              <li
                key={assignment.id}
                className="rounded-lg border border-border bg-surface-hover px-3 py-2 text-sm text-foreground/80"
              >
                {assignment.title}
              </li>
            ))}
          </ul>
        )
      )}

      <form onSubmit={handleSubmit} className="space-y-3 rounded-xl border border-border bg-surface p-4">
        <input
          type="text"
          required
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Assignment title"
          className={authInputClass}
        />
        <textarea
          required
          rows={3}
          value={instructions}
          onChange={(e) => setInstructions(e.target.value)}
          placeholder="Instructions for students"
          className={authInputClass}
        />
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <input
            type="datetime-local"
            value={dueAt}
            onChange={(e) => setDueAt(e.target.value)}
            className={authInputClass}
          />
          <label className="flex items-center gap-2 text-sm text-foreground/70">
            <input
              type="checkbox"
              checked={allowLate}
              onChange={(e) => setAllowLate(e.target.checked)}
              className="h-4 w-4 rounded border-border-strong"
            />
            Allow late submissions
          </label>
        </div>

        {error && <p className="text-sm text-rose-400">{error}</p>}

        <button
          type="submit"
          disabled={submitting || !title.trim() || !instructions.trim()}
          className="rounded-full bg-teal-400 px-4 py-1.5 text-sm font-semibold text-emerald-950 transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {submitting ? "Creating…" : "Create assignment"}
        </button>
      </form>
    </div>
  );
}
