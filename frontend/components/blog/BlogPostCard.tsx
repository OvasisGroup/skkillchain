import { Newspaper } from "lucide-react";
import Link from "next/link";
import type { BlogPost } from "@/lib/api/types";

function authorName(post: BlogPost): string {
  const name = `${post.author.profile.first_name} ${post.author.profile.last_name}`.trim();
  return name || post.author.email;
}

function formatDate(value: string): string {
  return new Date(value).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function BlogPostCard({ post }: { post: BlogPost }) {
  return (
    <Link
      href={`/blog/${post.slug}`}
      className="group flex flex-col overflow-hidden rounded-2xl border border-border bg-surface shadow-sm transition-all hover:-translate-y-0.5 hover:border-teal-400/50 hover:bg-surface-hover hover:shadow-md"
    >
      <div className="relative flex aspect-video items-center justify-center overflow-hidden bg-emerald-500">
        {post.cover_image ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={post.cover_image}
            alt=""
            className="absolute inset-0 h-full w-full object-cover"
          />
        ) : (
          <Newspaper className="h-10 w-10 text-teal-950/80" strokeWidth={1.5} />
        )}
      </div>
      <div className="flex flex-1 flex-col p-5">
        {post.tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5 text-xs uppercase tracking-wide text-foreground/40">
            {post.tags.slice(0, 3).map((tag) => (
              <span key={tag.id}>{tag.name}</span>
            ))}
          </div>
        )}
        <h3 className="mt-3 text-base font-semibold text-foreground group-hover:text-teal-600 dark:group-hover:text-teal-300">
          {post.title}
        </h3>
        {post.summary && (
          <p className="mt-1.5 line-clamp-2 flex-1 text-sm text-foreground/60">{post.summary}</p>
        )}
        <div className="mt-4 flex items-center justify-between border-t border-border pt-4 text-xs text-foreground/50">
          <span>{authorName(post)}</span>
          {post.published_at && <span>{formatDate(post.published_at)}</span>}
        </div>
      </div>
    </Link>
  );
}
