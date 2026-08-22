import { ArrowRight } from "lucide-react";
import Link from "next/link";
import { BlogPostCard } from "@/components/blog/BlogPostCard";
import { listBlogPosts } from "@/lib/api/blog";
import { Reveal } from "@/components/animation/Reveal";

const FEATURED_COUNT = 3;

export async function BlogHighlights() {
  // Landing content, not a data page — if the API is unreachable or nobody
  // has published a post yet, skip the section entirely rather than show
  // an empty/error block on the homepage. Same shape as Instructors.
  const posts = await listBlogPosts()
    .then((page) => page.results)
    .catch(() => []);
  if (posts.length === 0) return null;

  return (
    <section className="mx-auto max-w-7xl px-6 py-24">
      <Reveal className="mx-auto max-w-4xl text-center">
        <p className="text-sm font-semibold uppercase tracking-wider text-lime-400">Blog</p>
        <h2 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          From the SkillChain blog
        </h2>
        <p className="mt-4 text-lg text-foreground/60">
          News, guides, and updates from the team.
        </p>
      </Reveal>

      <Reveal
        className="mx-auto mt-16 grid max-w-2xl grid-cols-1 gap-6 sm:grid-cols-2 lg:max-w-none lg:grid-cols-3"
        stagger={0.1}
      >
        {posts.slice(0, FEATURED_COUNT).map((post) => (
          <BlogPostCard key={post.id} post={post} />
        ))}
      </Reveal>

      <div className="mt-10 text-center">
        <Link
          href="/blog"
          className="group inline-flex items-center gap-2 text-sm font-semibold text-teal-400 hover:text-teal-300"
        >
          Visit the blog
          <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
        </Link>
      </div>
    </section>
  );
}
