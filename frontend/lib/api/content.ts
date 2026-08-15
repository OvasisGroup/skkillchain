import { apiFetch } from "./client";
import type { CursorPage, Lesson, Section } from "./types";

export interface SectionCreateInput {
  title: string;
  sort_order?: number;
}

export interface LessonCreateInput {
  title: string;
  lesson_type: Lesson["lesson_type"];
  sort_order?: number;
  duration_seconds?: number;
  is_preview?: boolean;
  // Only meaningful when lesson_type is "video" or "pdf" — and only one of
  // content_file/video_url at a time for a video lesson (the backend
  // rejects both being set together).
  content_file?: File;
  video_url?: string;
  // Only meaningful when lesson_type is "article".
  article_body?: string;
}

function lessonFormData(input: LessonCreateInput): FormData {
  const form = new FormData();
  form.set("title", input.title);
  form.set("lesson_type", input.lesson_type);
  form.set("sort_order", String(input.sort_order ?? 0));
  form.set("duration_seconds", String(input.duration_seconds ?? 0));
  form.set("is_preview", String(input.is_preview ?? false));
  if (input.content_file) form.set("content_file", input.content_file);
  if (input.video_url) form.set("video_url", input.video_url);
  if (input.article_body) form.set("article_body", input.article_body);
  return form;
}

// Cursor-paginated (page_size 20) — a course with more sections than that won't
// show the rest here yet, since there's no "load more" wired up.
export async function listSections(courseId: string, token: string): Promise<Section[]> {
  const page = await apiFetch<CursorPage<Section>>(`/instructor/courses/${courseId}/sections/`, {
    token,
    cache: "no-store",
  });
  return page.results;
}

export function createSection(
  courseId: string,
  input: SectionCreateInput,
  token: string
): Promise<Section> {
  return apiFetch<Section>(`/instructor/courses/${courseId}/sections/`, {
    method: "POST",
    token,
    body: input,
  });
}

// Same cursor-pagination caveat as listSections.
export async function listLessons(sectionId: string, token: string): Promise<Lesson[]> {
  const page = await apiFetch<CursorPage<Lesson>>(`/instructor/sections/${sectionId}/lessons/`, {
    token,
    cache: "no-store",
  });
  return page.results;
}

export function createLesson(
  sectionId: string,
  input: LessonCreateInput,
  token: string
): Promise<Lesson> {
  return apiFetch<Lesson>(`/instructor/sections/${sectionId}/lessons/`, {
    method: "POST",
    token,
    body: input.content_file ? lessonFormData(input) : input,
  });
}

// Attaches or replaces a lesson's video/PDF file after creation.
export function uploadLessonContent(
  lessonId: string,
  file: File,
  token: string
): Promise<Lesson> {
  const form = new FormData();
  form.set("content_file", file);
  return apiFetch<Lesson>(`/instructor/lessons/${lessonId}/`, {
    method: "PATCH",
    token,
    body: form,
  });
}
