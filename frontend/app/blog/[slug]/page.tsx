import Link from "next/link";
import { notFound } from "next/navigation";
import { ShareButtons } from "@/components/blog/ShareButtons";
import { ApiError } from "@/lib/api/client";
import { getBlogPost } from "@/lib/api/blog";
import type { BlogPostDetail } from "@/lib/api/types";
import { SITE_NAME, absoluteUrl, safeJsonLd } from "@/lib/seo";
import { Reveal } from "@/components/animation/Reveal";

function authorName(post: BlogPostDetail): string {
  const name = `${post.author.profile.first_name} ${post.author.profile.last_name}`.trim();
  return name || post.author.email;
}

function formatDate(value: string): string {
  return new Date(value).toLocaleDateString(undefined, {
    month: "long",
    day: "numeric",
    year: "numeric",
  });
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  try {
    const post = await getBlogPost(slug);
    const canonical = `/blog/${post.slug}`;
    return {
      title: post.title,
      description: post.summary || undefined,
      alternates: { canonical },
      openGraph: {
        type: "article",
        url: absoluteUrl(canonical),
        title: post.title,
        description: post.summary,
        ...(post.cover_image ? { images: [{ url: post.cover_image }] } : {}),
      },
    };
  } catch {
    return { title: "Blog" };
  }
}

function blogPostJsonLd(post: BlogPostDetail) {
  return {
    "@context": "https://schema.org",
    "@type": "BlogPosting",
    headline: post.title,
    description: post.summary,
    url: absoluteUrl(`/blog/${post.slug}`),
    datePublished: post.published_at,
    dateModified: post.updated_at,
    author: { "@type": "Person", name: authorName(post) },
    publisher: { "@type": "Organization", name: SITE_NAME },
    ...(post.cover_image ? { image: post.cover_image } : {}),
  };
}

export default async function BlogPostPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;

  let post: BlogPostDetail;
  try {
    post = await getBlogPost(slug);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) {
      notFound();
    }
    throw err;
  }

  const shareUrl = absoluteUrl(`/blog/${post.slug}`);

  return (
    <div className="mx-auto max-w-3xl px-6 py-16">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: safeJsonLd(blogPostJsonLd(post)) }}
      />
      <nav className="text-sm text-foreground/40">
        <Link href="/blog" className="hover:text-foreground">
          Blog
        </Link>
        <span className="mx-2">/</span>
        <span className="text-foreground">{post.title}</span>
      </nav>

      <Reveal>
        {post.tags.length > 0 && (
          <div className="mt-6 flex flex-wrap gap-2">
            {post.tags.map((tag) => (
              <Link
                key={tag.id}
                href={`/blog?tag=${tag.slug}`}
                className="rounded-full border border-border-strong px-2.5 py-0.5 text-xs font-medium text-foreground/70 hover:bg-surface-hover"
              >
                {tag.name}
              </Link>
            ))}
          </div>
        )}

        <h1 className="mt-4 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          {post.title}
        </h1>

        <div className="mt-4 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            {post.author.profile.avatar ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={post.author.profile.avatar}
                alt=""
                className="h-10 w-10 rounded-full object-cover"
              />
            ) : (
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-teal-400/15 text-sm font-semibold text-teal-500 dark:text-teal-300">
                {authorName(post).charAt(0).toUpperCase()}
              </div>
            )}
            <div className="text-sm">
              <p className="font-medium text-foreground">{authorName(post)}</p>
              {post.published_at && (
                <p className="text-foreground/50">{formatDate(post.published_at)}</p>
              )}
            </div>
          </div>
          <ShareButtons url={shareUrl} title={post.title} />
        </div>
      </Reveal>

      {post.cover_image && (
        <Reveal className="mt-8 overflow-hidden rounded-2xl border border-border">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={post.cover_image} alt="" className="aspect-video w-full object-cover" />
        </Reveal>
      )}

      <Reveal className="mt-10">
        <div className="space-y-6 text-base leading-8 text-foreground/80">
          {post.body
            .split(/\n{2,}/)
            .filter((paragraph) => paragraph.trim().length > 0)
            .map((paragraph, index) => (
              <p key={index} className="whitespace-pre-line">
                {paragraph}
              </p>
            ))}
        </div>
      </Reveal>

      <div className="mt-12 flex items-center justify-between border-t border-border pt-6">
        <Link href="/blog" className="text-sm font-medium text-foreground/60 hover:text-foreground">
          ← Back to blog
        </Link>
        <ShareButtons url={shareUrl} title={post.title} />
      </div>
    </div>
  );
}
