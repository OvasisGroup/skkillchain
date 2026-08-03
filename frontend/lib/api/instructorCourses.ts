import { apiFetch } from "./client";
import type { Coupon, Course, CourseDetail, CourseWriteResult, CursorPage } from "./types";

export interface CourseCreateInput {
  title: string;
  summary?: string;
  description?: string;
  language?: string;
  difficulty?: "beginner" | "intermediate" | "advanced";
  price_amount?: string;
  currency?: string;
  category_id: string;
  tag_ids?: string[];
  prerequisites?: string[];
  learning_objectives?: string[];
  cover_image?: File;
}

function courseFormData(input: CourseCreateInput): FormData {
  const form = new FormData();
  form.set("title", input.title);
  if (input.summary !== undefined) form.set("summary", input.summary);
  if (input.description !== undefined) form.set("description", input.description);
  if (input.language !== undefined) form.set("language", input.language);
  if (input.difficulty !== undefined) form.set("difficulty", input.difficulty);
  if (input.price_amount !== undefined) form.set("price_amount", input.price_amount);
  if (input.currency !== undefined) form.set("currency", input.currency);
  form.set("category_id", input.category_id);
  input.tag_ids?.forEach((id) => form.append("tag_ids", id));
  input.prerequisites?.forEach((text) => form.append("prerequisites", text));
  input.learning_objectives?.forEach((text) => form.append("learning_objectives", text));
  if (input.cover_image) form.set("cover_image", input.cover_image);
  return form;
}

export function listInstructorCourses(token: string): Promise<CursorPage<Course>> {
  return apiFetch<CursorPage<Course>>("/instructor/courses/", { token, cache: "no-store" });
}

export function getInstructorCourse(courseId: string, token: string): Promise<CourseWriteResult> {
  return apiFetch<CourseWriteResult>(`/instructor/courses/${courseId}/`, {
    token,
    cache: "no-store",
  });
}

export function createCourse(input: CourseCreateInput, token: string): Promise<CourseWriteResult> {
  return apiFetch<CourseWriteResult>("/instructor/courses/", {
    method: "POST",
    token,
    body: input.cover_image ? courseFormData(input) : input,
  });
}

// Attaches or replaces a course's cover image after creation.
export function uploadCourseCoverImage(
  courseId: string,
  file: File,
  token: string
): Promise<CourseWriteResult> {
  const form = new FormData();
  form.set("cover_image", file);
  return apiFetch<CourseWriteResult>(`/instructor/courses/${courseId}/`, {
    method: "PATCH",
    token,
    body: form,
  });
}

export function submitCourseForReview(courseId: string, token: string): Promise<CourseDetail> {
  return apiFetch<CourseDetail>(`/instructor/courses/${courseId}/submit-review/`, {
    method: "POST",
    token,
  });
}

export function publishCourse(courseId: string, token: string): Promise<CourseDetail> {
  return apiFetch<CourseDetail>(`/instructor/courses/${courseId}/publish/`, {
    method: "POST",
    token,
  });
}

export function createCourseCoupon(
  courseId: string,
  body: Pick<Coupon, "code" | "discount_type" | "discount_value"> &
    Partial<Pick<Coupon, "valid_from" | "valid_to" | "usage_limit" | "per_user_limit">>,
  token: string
): Promise<Coupon> {
  return apiFetch<Coupon>(`/instructor/courses/${courseId}/coupons/`, {
    method: "POST",
    token,
    body,
  });
}
