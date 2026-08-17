import { apiFetch } from "./client";
import type { CourseCreateInput } from "./instructorCourses";
import type { Course, CourseDetail, CourseWriteResult, CursorPage } from "./types";

// Admin counterpart to lib/api/instructorCourses.ts — same shapes, but
// scoped by the courses.manage permission instead of ownership, so an
// admin can list/edit/create any course regardless of who owns it. See
// backend/apps/catalog/views.py's "Admin course management" section.

export interface AdminCourseCreateInput extends CourseCreateInput {
  owner_id: string;
}

function courseFormData(input: AdminCourseCreateInput): FormData {
  const form = new FormData();
  form.set("title", input.title);
  if (input.summary !== undefined) form.set("summary", input.summary);
  if (input.description !== undefined) form.set("description", input.description);
  if (input.language !== undefined) form.set("language", input.language);
  if (input.difficulty !== undefined) form.set("difficulty", input.difficulty);
  if (input.price_amount !== undefined) form.set("price_amount", input.price_amount);
  if (input.currency !== undefined) form.set("currency", input.currency);
  form.set("category_id", input.category_id);
  form.set("owner_id", input.owner_id);
  input.tag_ids?.forEach((id) => form.append("tag_ids", id));
  input.prerequisites?.forEach((text) => form.append("prerequisites", text));
  input.learning_objectives?.forEach((text) => form.append("learning_objectives", text));
  if (input.cover_image) form.set("cover_image", input.cover_image);
  return form;
}

export function listAdminCourses(
  token: string,
  filters?: { status?: string; category?: string; language?: string; difficulty?: string; q?: string }
): Promise<CursorPage<Course>> {
  const query = new URLSearchParams(
    Object.entries(filters ?? {}).filter(([, v]) => v !== undefined && v !== "")
  ).toString();
  return apiFetch<CursorPage<Course>>(`/admin/courses/${query ? `?${query}` : ""}`, {
    token,
    cache: "no-store",
  });
}

// Full read shape (nested category/tags, prerequisites/objectives as
// plain strings) — the admin edit form pre-fills from this, not from
// CourseWriteResult, since prerequisites/learning_objectives are
// write_only on the write serializer used for PATCH (see backend
// AdminCourseDetailView.get_serializer_class).
export function getAdminCourse(courseId: string, token: string): Promise<CourseDetail> {
  return apiFetch<CourseDetail>(`/admin/courses/${courseId}/`, { token, cache: "no-store" });
}

export function createAdminCourse(
  input: AdminCourseCreateInput,
  token: string
): Promise<CourseWriteResult> {
  return apiFetch<CourseWriteResult>("/admin/courses/", {
    method: "POST",
    token,
    body: input.cover_image ? courseFormData(input) : input,
  });
}

export function updateAdminCourse(
  courseId: string,
  input: Partial<CourseCreateInput>,
  token: string
): Promise<CourseWriteResult> {
  return apiFetch<CourseWriteResult>(`/admin/courses/${courseId}/`, {
    method: "PATCH",
    token,
    body: input,
  });
}

export function uploadAdminCourseCoverImage(
  courseId: string,
  file: File,
  token: string
): Promise<CourseWriteResult> {
  const form = new FormData();
  form.set("cover_image", file);
  return apiFetch<CourseWriteResult>(`/admin/courses/${courseId}/`, {
    method: "PATCH",
    token,
    body: form,
  });
}

export function deleteAdminCourse(courseId: string, token: string): Promise<void> {
  return apiFetch<void>(`/admin/courses/${courseId}/`, { method: "DELETE", token });
}

export type NotifyAudience = "instructor" | "students" | "both";

export interface NotifyResult {
  audience: NotifyAudience;
  subject: string;
  message: string;
}

export function notifyCourseRecipients(
  courseId: string,
  input: NotifyResult,
  token: string
): Promise<NotifyResult> {
  return apiFetch<NotifyResult>(`/admin/courses/${courseId}/notify/`, {
    method: "POST",
    token,
    body: input,
  });
}
