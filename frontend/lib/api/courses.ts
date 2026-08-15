import { apiFetch } from "./client";
import type { Category, Course, CourseDetail, CursorPage, PreviewSection, Tag } from "./types";

export function listCourses(params?: {
  category?: string;
  language?: string;
  difficulty?: string;
  q?: string;
  is_free?: boolean;
}): Promise<CursorPage<Course>> {
  const query = params
    ? new URLSearchParams(
        Object.entries(params)
          .filter(([, v]) => v !== undefined && v !== "")
          .map(([k, v]) => [k, String(v)])
      ).toString()
    : "";
  return apiFetch<CursorPage<Course>>(`/courses/${query ? `?${query}` : ""}`, {
    cache: "no-store",
  });
}

// Unwraps the first page for callers that just want a flat list (the
// homepage's featured strip) — mirrors listInstructors()'s shape so both
// landing sections fetch identically instead of one juggling pagination.
export function listFeaturedCourses(): Promise<Course[]> {
  return listCourses().then((page) => page.results);
}

export function listCategories(): Promise<Category[]> {
  return apiFetch<Category[]>("/categories/", { cache: "no-store" });
}

export function listTags(): Promise<Tag[]> {
  return apiFetch<Tag[]>("/tags/", { cache: "no-store" });
}

// Creates a tag, or returns the existing one if a tag with the same name
// (case-insensitive) already exists — lets an instructor add a brand-new
// tag inline while authoring a course without risking near-duplicates.
export function createTag(name: string, token: string): Promise<Tag> {
  return apiFetch<Tag>("/tags/", { method: "POST", token, body: { name } });
}

export function getCourse(id: string): Promise<CourseDetail> {
  return apiFetch<CourseDetail>(`/courses/${id}/`, { cache: "no-store" });
}

export function getCoursePreview(id: string): Promise<PreviewSection[]> {
  return apiFetch<PreviewSection[]>(`/courses/${id}/preview/`, { cache: "no-store" });
}
