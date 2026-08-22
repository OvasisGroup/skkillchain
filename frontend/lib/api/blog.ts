import { apiFetch } from "./client";
import type {
  BlogPost,
  BlogPostCreateInput,
  BlogPostDetail,
  BlogPostUpdateInput,
  BlogPostWriteResult,
  BlogTag,
  CursorPage,
} from "./types";

// ---------- Public ----------

export function listBlogPosts(params: { tag?: string } = {}): Promise<CursorPage<BlogPost>> {
  const query = new URLSearchParams();
  if (params.tag) query.set("tag", params.tag);
  const qs = query.toString();
  return apiFetch<CursorPage<BlogPost>>(`/blog/posts/${qs ? `?${qs}` : ""}`, {
    cache: "no-store",
  });
}

export function getBlogPost(slug: string): Promise<BlogPostDetail> {
  return apiFetch<BlogPostDetail>(`/blog/posts/${slug}/`, { cache: "no-store" });
}

export function listBlogTags(): Promise<BlogTag[]> {
  return apiFetch<BlogTag[]>("/blog/tags/", { cache: "no-store" });
}

// Idempotent: returns the existing tag if the name already exists (case-
// insensitive) rather than erroring — same as apps.catalog's course-tag
// endpoint, see backend/apps/cms/views.py.
export function createBlogTag(name: string, token: string): Promise<BlogTag> {
  return apiFetch<BlogTag>("/blog/tags/", { method: "POST", token, body: { name } });
}

// ---------- Author (self-service authoring, used by a future dashboard UI) ----------

export function listMyBlogPosts(token: string): Promise<CursorPage<BlogPost>> {
  return apiFetch<CursorPage<BlogPost>>("/authors/me/blog-posts/", { token, cache: "no-store" });
}

export function createBlogPost(
  input: BlogPostCreateInput,
  token: string
): Promise<BlogPostWriteResult> {
  return apiFetch<BlogPostWriteResult>("/authors/me/blog-posts/", {
    method: "POST",
    token,
    body: input,
  });
}

export function updateBlogPost(
  postId: string,
  input: BlogPostUpdateInput,
  token: string
): Promise<BlogPostWriteResult> {
  return apiFetch<BlogPostWriteResult>(`/authors/me/blog-posts/${postId}/`, {
    method: "PATCH",
    token,
    body: input,
  });
}

export function deleteBlogPost(postId: string, token: string): Promise<void> {
  return apiFetch<void>(`/authors/me/blog-posts/${postId}/`, { method: "DELETE", token });
}

export function publishBlogPost(postId: string, token: string): Promise<BlogPost> {
  return apiFetch<BlogPost>(`/authors/me/blog-posts/${postId}/publish/`, {
    method: "POST",
    token,
  });
}

export function unpublishBlogPost(postId: string, token: string): Promise<BlogPost> {
  return apiFetch<BlogPost>(`/authors/me/blog-posts/${postId}/unpublish/`, {
    method: "POST",
    token,
  });
}
