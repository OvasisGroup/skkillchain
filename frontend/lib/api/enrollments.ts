import { apiFetch } from "./client";
import type {
  Certificate,
  CurriculumSection,
  CursorPage,
  Enrollment,
  EnrollmentProgress,
  GradeEntry,
  LessonContent,
  ProgressEntry,
  ProgressUpdateInput,
  WishlistItem,
} from "./types";

export function enroll(courseId: string, token: string): Promise<Enrollment> {
  return apiFetch<Enrollment>("/enrollments/", {
    method: "POST",
    token,
    body: { course_id: courseId },
  });
}

export function listMyCourses(token: string): Promise<CursorPage<Enrollment>> {
  return apiFetch<CursorPage<Enrollment>>("/students/me/courses/", { token, cache: "no-store" });
}

export function listContinueLearning(token: string): Promise<Enrollment[]> {
  return apiFetch<Enrollment[]>("/students/me/continue-learning/", { token, cache: "no-store" });
}

export function listWishlist(token: string): Promise<WishlistItem[]> {
  return apiFetch<WishlistItem[]>("/students/me/wishlist/", { token, cache: "no-store" });
}

export function addToWishlist(courseId: string, token: string): Promise<void> {
  return apiFetch<void>(`/students/me/wishlist/${courseId}/`, { method: "POST", token });
}

export function removeFromWishlist(courseId: string, token: string): Promise<void> {
  return apiFetch<void>(`/students/me/wishlist/${courseId}/`, { method: "DELETE", token });
}

export function getProgress(enrollmentId: string, token: string): Promise<EnrollmentProgress> {
  return apiFetch<EnrollmentProgress>(`/progress/${enrollmentId}/`, { token, cache: "no-store" });
}

export function updateProgress(
  input: ProgressUpdateInput,
  token: string
): Promise<ProgressEntry> {
  return apiFetch<ProgressEntry>("/progress/", { method: "POST", token, body: input });
}

export function getCourseCurriculum(
  courseId: string,
  token: string
): Promise<CurriculumSection[]> {
  return apiFetch<CurriculumSection[]>(`/courses/${courseId}/curriculum/`, {
    token,
    cache: "no-store",
  });
}

export function getLessonContent(lessonId: string, token: string): Promise<LessonContent> {
  return apiFetch<LessonContent>(`/lessons/${lessonId}/content/`, { token, cache: "no-store" });
}

export function listMyGrades(token: string): Promise<GradeEntry[]> {
  return apiFetch<GradeEntry[]>("/students/me/grades/", { token, cache: "no-store" });
}

export function listCertificates(token: string): Promise<CursorPage<Certificate>> {
  return apiFetch<CursorPage<Certificate>>("/certificates/", { token, cache: "no-store" });
}
