"use client";

import { MessageSquare } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { ApiError } from "@/lib/api/client";
import { postCourseDiscussion } from "@/lib/api/discussions";
import type { DiscussionPost } from "@/lib/api/types";
import { useAuth } from "@/lib/auth/AuthContext";

export function CourseDiscussion({
  courseId,
  initialPosts,
}: {
  courseId: string;
  initialPosts: DiscussionPost[];
}) {
  const { accessToken, isAuthenticated } = useAuth();
  const [posts, setPosts] = useState(initialPosts);
  const [body, setBody] = useState("");
  const [posting, setPosting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!accessToken || !body.trim()) return;
    setPosting(true);
    setError(null);
    try {
      const post = await postCourseDiscussion(courseId, body, accessToken);
      setPosts((prev) => [...prev, post]);
      setBody("");
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message_ : "Couldn't post your message. Please try again."
      );
    } finally {
      setPosting(false);
    }
  }

  return (
    <div className="mt-10">
      <h2 className="flex items-center gap-2 text-lg font-semibold text-foreground">
        <MessageSquare className="h-5 w-5 text-teal-400" />
        Discussion
      </h2>

      <div className="mt-4 space-y-3">
        {posts.length === 0 ? (
          <p className="text-sm text-foreground/50">
            No posts yet — be the first to ask a question or share something.
          </p>
        ) : (
          posts.map((post) => (
            <div key={post.id} className="rounded-xl border border-border bg-surface p-4">
              <div className="flex items-center justify-between gap-3">
                <span className="text-sm font-semibold text-foreground">{post.user_email}</span>
                <span className="text-xs text-foreground/40">
                  {new Date(post.created_at).toLocaleString()}
                </span>
              </div>
              <p className="mt-2 whitespace-pre-line text-sm text-foreground/70">{post.body}</p>
            </div>
          ))
        )}
      </div>

      <div className="mt-4">
        {isAuthenticated ? (
          <form onSubmit={handleSubmit} className="space-y-2">
            <textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              placeholder="Ask a question or share something with this course…"
              rows={3}
              className="w-full rounded-xl border border-border-strong bg-surface px-3 py-2 text-sm text-foreground focus:border-teal-400 focus:outline-none"
            />
            {error && <p className="text-xs text-rose-400">{error}</p>}
            <button
              type="submit"
              disabled={posting || !body.trim()}
              className="rounded-full bg-teal-400 px-5 py-2 text-sm font-semibold text-emerald-950 transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {posting ? "Posting…" : "Post"}
            </button>
          </form>
        ) : (
          <p className="text-sm text-foreground/50">
            <Link
              href={`/login?next=${encodeURIComponent(`/courses/${courseId}`)}`}
              className="text-teal-400 hover:underline"
            >
              Log in
            </Link>{" "}
            to join the discussion.
          </p>
        )}
      </div>
    </div>
  );
}
