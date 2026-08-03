import { apiFetch } from "./client";
import type { Course, CourseDetail, CursorPage } from "./types";

export function listPendingCourses(token: string): Promise<CursorPage<Course>> {
  return apiFetch<CursorPage<Course>>("/admin/courses/pending-review/", {
    token,
    cache: "no-store",
  });
}

export function approveCourse(courseId: string, token: string): Promise<CourseDetail> {
  return apiFetch<CourseDetail>(`/admin/courses/${courseId}/approve/`, {
    method: "POST",
    token,
  });
}

export function rejectCourse(
  courseId: string,
  reason: string,
  token: string
): Promise<CourseDetail> {
  return apiFetch<CourseDetail>(`/admin/courses/${courseId}/reject/`, {
    method: "POST",
    token,
    body: { reason },
  });
}
