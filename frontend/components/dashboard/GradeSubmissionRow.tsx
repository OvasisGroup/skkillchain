"use client";

import { useState } from "react";
import { ApiError } from "@/lib/api/client";
import { gradeSubmission } from "@/lib/api/grading";
import type { AssignmentSubmission } from "@/lib/api/types";
import { useAuth } from "@/lib/auth/AuthContext";

export function GradeSubmissionRow({
  assignmentId,
  assignmentTitle,
  submission,
  onGraded,
}: {
  assignmentId: string;
  assignmentTitle: string;
  submission: AssignmentSubmission;
  onGraded: (submissionId: string) => void;
}) {
  const { accessToken } = useAuth();
  const [grade, setGrade] = useState("");
  const [feedback, setFeedback] = useState("");
  const [status, setStatus] = useState<"idle" | "saving" | "error">("idle");
  const [error, setError] = useState<string | null>(null);

  async function handleSave() {
    if (!accessToken) return;
    const gradeValue = Number(grade);
    if (Number.isNaN(gradeValue) || gradeValue < 0 || gradeValue > 100) {
      setError("Enter a grade between 0 and 100.");
      setStatus("error");
      return;
    }
    setStatus("saving");
    setError(null);
    try {
      await gradeSubmission(
        assignmentId,
        submission.id,
        { grade: gradeValue, feedback: feedback || undefined },
        accessToken
      );
      onGraded(submission.id);
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't save this grade.");
      setStatus("error");
    }
  }

  return (
    <tr className="border-b border-border last:border-0">
      <td className="px-4 py-3 align-top text-sm text-foreground">{assignmentTitle}</td>
      <td className="px-4 py-3 align-top text-sm text-foreground/70">
        {submission.student_email}
      </td>
      <td className="max-w-xs truncate px-4 py-3 align-top text-sm">
        <a
          href={submission.content_ref}
          target="_blank"
          rel="noreferrer"
          className="text-teal-400 hover:underline"
        >
          {submission.content_ref}
        </a>
      </td>
      <td className="px-4 py-3 align-top">
        <div className="flex flex-wrap items-center gap-2">
          <input
            type="number"
            min={0}
            max={100}
            value={grade}
            onChange={(e) => setGrade(e.target.value)}
            placeholder="0-100"
            className="w-20 rounded-lg border border-border-strong bg-surface px-2 py-1 text-sm text-foreground focus:border-teal-400 focus:outline-none"
          />
          <input
            type="text"
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="Feedback (optional)"
            className="min-w-[10rem] flex-1 rounded-lg border border-border-strong bg-surface px-2 py-1 text-sm text-foreground focus:border-teal-400 focus:outline-none"
          />
          <button
            type="button"
            onClick={handleSave}
            disabled={status === "saving" || !grade}
            className="rounded-lg bg-teal-400 px-3 py-1 text-sm font-semibold text-emerald-950 transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {status === "saving" ? "Saving…" : "Save"}
          </button>
        </div>
        {error && <p className="mt-1 text-xs text-rose-400">{error}</p>}
      </td>
    </tr>
  );
}
