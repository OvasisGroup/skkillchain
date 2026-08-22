import type { MetadataRoute } from "next";
import { API_BASE_URL, apiFetch } from "@/lib/api/client";
import { listInstructors } from "@/lib/api/instructors";
import type { BlogPost, Course, CursorPage } from "@/lib/api/types";
import { absoluteUrl } from "@/lib/seo";

const STATIC_ROUTES: Array<{ path: string; changeFrequency: MetadataRoute.Sitemap[number]["changeFrequency"]; priority: number }> = [
  { path: "/", changeFrequency: "daily", priority: 1 },
  { path: "/courses", changeFrequency: "daily", priority: 0.9 },
  { path: "/instructors", changeFrequency: "weekly", priority: 0.7 },
  { path: "/live-sessions", changeFrequency: "weekly", priority: 0.7 },
  { path: "/blog", changeFrequency: "daily", priority: 0.7 },
  { path: "/about", changeFrequency: "monthly", priority: 0.5 },
  { path: "/changamka", changeFrequency: "monthly", priority: 0.7 },
  { path: "/help", changeFrequency: "monthly", priority: 0.4 },
  { path: "/contact", changeFrequency: "monthly", priority: 0.4 },
  { path: "/privacy", changeFrequency: "yearly", priority: 0.3 },
  { path: "/terms", changeFrequency: "yearly", priority: 0.3 },
];

// Cursor-paginated, so the sitemap has to walk `next` links itself; capped
// well above any catalog size we expect so a pagination bug can't spin
// forever during a build.
async function fetchAllCourses(): Promise<Course[]> {
  const courses: Course[] = [];
  let path: string | null = "/courses/";

  for (let guard = 0; path && guard < 100; guard++) {
    const page: CursorPage<Course> = await apiFetch<CursorPage<Course>>(path, {
      cache: "no-store",
    });
    courses.push(...page.results);
    path = page.next ? page.next.replace(API_BASE_URL, "") : null;
  }

  return courses;
}

// Cursor-paginated, same walk-the-`next`-link approach as fetchAllCourses —
// the public list endpoint already only returns published posts.
async function fetchAllBlogPosts(): Promise<BlogPost[]> {
  const posts: BlogPost[] = [];
  let path: string | null = "/blog/posts/";

  for (let guard = 0; path && guard < 100; guard++) {
    const page: CursorPage<BlogPost> = await apiFetch<CursorPage<BlogPost>>(path, {
      cache: "no-store",
    });
    posts.push(...page.results);
    path = page.next ? page.next.replace(API_BASE_URL, "") : null;
  }

  return posts;
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const staticEntries: MetadataRoute.Sitemap = STATIC_ROUTES.map((route) => ({
    url: absoluteUrl(route.path),
    changeFrequency: route.changeFrequency,
    priority: route.priority,
  }));

  // The backend being unreachable at build time shouldn't take down the
  // whole sitemap — fall back to the static routes only.
  const [courses, instructors, blogPosts] = await Promise.all([
    fetchAllCourses().catch(() => []),
    listInstructors().catch(() => []),
    fetchAllBlogPosts().catch(() => []),
  ]);

  const courseEntries: MetadataRoute.Sitemap = courses
    .filter((course) => course.status === "published")
    .map((course) => ({
      url: absoluteUrl(`/courses/${course.id}`),
      lastModified: course.published_at ?? undefined,
      changeFrequency: "weekly",
      priority: 0.8,
    }));

  const instructorEntries: MetadataRoute.Sitemap = instructors.map((instructor) => ({
    url: absoluteUrl(`/instructors/${instructor.id}`),
    changeFrequency: "monthly",
    priority: 0.5,
  }));

  const blogPostEntries: MetadataRoute.Sitemap = blogPosts.map((post) => ({
    url: absoluteUrl(`/blog/${post.slug}`),
    lastModified: post.published_at ?? undefined,
    changeFrequency: "monthly",
    priority: 0.6,
  }));

  return [...staticEntries, ...courseEntries, ...instructorEntries, ...blogPostEntries];
}
