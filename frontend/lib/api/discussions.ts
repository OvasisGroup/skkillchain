import { apiFetch } from "./client";
import type { CursorPage, DiscussionPost } from "./types";

export function listCourseDiscussions(courseId: string): Promise<CursorPage<DiscussionPost>> {
  return apiFetch<CursorPage<DiscussionPost>>(`/courses/${courseId}/discussions/`, {
    cache: "no-store",
  });
}

export function postCourseDiscussion(
  courseId: string,
  body: string,
  token: string
): Promise<DiscussionPost> {
  return apiFetch<DiscussionPost>(`/courses/${courseId}/discussions/`, {
    method: "POST",
    token,
    body: { body },
  });
}
