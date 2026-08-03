import { apiFetch } from "./client";
import type { Assignment, AssignmentGradeRequest, AssignmentSubmission } from "./types";

export function listCourseAssignments(courseId: string, token: string): Promise<Assignment[]> {
  return apiFetch<Assignment[]>(`/instructor/courses/${courseId}/assignments/`, {
    token,
    cache: "no-store",
  });
}

export function listAssignmentSubmissions(
  assignmentId: string,
  token: string
): Promise<AssignmentSubmission[]> {
  return apiFetch<AssignmentSubmission[]>(`/instructor/assignments/${assignmentId}/submissions/`, {
    token,
    cache: "no-store",
  });
}

export function gradeSubmission(
  assignmentId: string,
  submissionId: string,
  body: AssignmentGradeRequest,
  token: string
): Promise<AssignmentSubmission> {
  return apiFetch<AssignmentSubmission>(
    `/instructor/assignments/${assignmentId}/submissions/${submissionId}/grade/`,
    { method: "POST", token, body }
  );
}

export function approveAiGrade(
  submissionId: string,
  token: string
): Promise<AssignmentSubmission> {
  return apiFetch<AssignmentSubmission>(
    `/assignments/submissions/${submissionId}/approve-ai-grade/`,
    { method: "POST", token }
  );
}
