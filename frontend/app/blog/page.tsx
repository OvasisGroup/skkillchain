import { AlertTriangle, Newspaper } from "lucide-react";
import Link from "next/link";
import { BlogPostCard } from "@/components/blog/BlogPostCard";
import { listBlogPosts, listBlogTags } from "@/lib/api/blog";
import type { BlogPost, BlogTag } from "@/lib/api/types";
import { Reveal } from "@/components/animation/Reveal";

export const metadata = {
  title: "Blog",
  description: "News, guides, and updates from the SkillChain team.",
  alternates: { canonical: "/blog" },
};

export default async function BlogPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = await searchParams;
  const activeTag = typeof params.tag === "string" ? params.tag : undefined;

  let posts: BlogPost[] = [];
  let tags: BlogTag[] = [];
  let loadError: string | null = null;

  try {
    const [postsPage, allTags] = await Promise.all([
      listBlogPosts({ tag: activeTag }),
      listBlogTags(),
    ]);
    posts = postsPage.results;
    tags = allTags;
  } catch {
    loadError = "We couldn't reach the blog API right now. Make sure it's running.";
  }

  return (
    <div className="mx-auto max-w-7xl px-6 py-16">
      <Reveal className="max-w-2xl">
        <p className="text-sm font-semibold uppercase tracking-wider text-lime-400">Blog</p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          News, guides, and updates
        </h1>
        <p className="mt-3 text-lg text-foreground/60">
          Stories from the SkillChain team — product updates, learning tips, and community
          highlights.
        </p>
      </Reveal>

      {tags.length > 0 && (
        <div className="mt-8 flex flex-wrap gap-2">
          <Link
            href="/blog"
            className={`rounded-full px-4 py-1.5 text-sm font-semibold transition-colors ${
              !activeTag
                ? "bg-teal-400 text-emerald-950"
                : "border border-border-strong text-foreground/70 hover:bg-surface-hover"
            }`}
          >
            All
          </Link>
          {tags.map((tag) => (
            <Link
              key={tag.id}
              href={`/blog?tag=${tag.slug}`}
              className={`rounded-full px-4 py-1.5 text-sm font-semibold transition-colors ${
                activeTag === tag.slug
                  ? "bg-teal-400 text-emerald-950"
                  : "border border-border-strong text-foreground/70 hover:bg-surface-hover"
              }`}
            >
              {tag.name}
            </Link>
          ))}
        </div>
      )}

      {loadError && (
        <div className="mt-10 flex items-start gap-3 rounded-xl border border-amber-500/20 bg-amber-500/10 p-4 text-sm text-amber-400">
          <AlertTriangle className="mt-0.5 h-5 w-5 flex-none" />
          <span>{loadError}</span>
        </div>
      )}

      {!loadError && posts.length === 0 && (
        <div className="mt-16 flex flex-col items-center rounded-2xl border border-dashed border-border-strong py-20 text-center">
          <Newspaper className="h-10 w-10 text-foreground/30" />
          <p className="mt-4 text-sm text-foreground/50">
            {activeTag ? "No posts with this tag yet." : "No posts published yet — check back soon."}
          </p>
        </div>
      )}

      {posts.length > 0 && (
        <div className="mt-8 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {posts.map((post) => (
            <BlogPostCard key={post.id} post={post} />
          ))}
        </div>
      )}
    </div>
  );
}
