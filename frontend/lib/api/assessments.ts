import { apiFetch } from "./client";
import type {
  AssignmentCreateInput,
  Assignment,
  CodingExerciseCreateInput,
  CodingExerciseDetail,
  QuizCreateInput,
  QuizDetail,
} from "./types";

// Quizzes and coding exercises have no instructor-facing list/retrieve endpoint
// yet — only creation. Callers keep whatever's returned from create in local
// state; there's currently no way to re-fetch them after a page reload.

export function createQuiz(
  courseId: string,
  input: QuizCreateInput,
  token: string
): Promise<QuizDetail> {
  return apiFetch<QuizDetail>(`/instructor/courses/${courseId}/quizzes/`, {
    method: "POST",
    token,
    body: input,
  });
}

export function createAssignment(
  courseId: string,
  input: AssignmentCreateInput,
  token: string
): Promise<Assignment> {
  return apiFetch<Assignment>(`/instructor/courses/${courseId}/assignments/`, {
    method: "POST",
    token,
    body: input,
  });
}

export function createCodingExercise(
  courseId: string,
  input: CodingExerciseCreateInput,
  token: string
): Promise<CodingExerciseDetail> {
  return apiFetch<CodingExerciseDetail>(`/instructor/courses/${courseId}/coding-exercises/`, {
    method: "POST",
    token,
    body: input,
  });
}
