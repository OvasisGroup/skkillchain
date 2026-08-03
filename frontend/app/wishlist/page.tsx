"use client";

import { Heart, HeartOff } from "lucide-react";
import Link from "next/link";
import { LoadingState } from "@/components/dashboard/DashboardStates";
import { useAuth } from "@/lib/auth/AuthContext";
import { useWishlist } from "@/lib/wishlist/WishlistContext";

export default function WishlistPage() {
  const { accessToken } = useAuth();
  const { items, toggle } = useWishlist();

  return (
    <div className="mx-auto max-w-7xl px-6 py-16">
      <div className="max-w-2xl">
        <p className="text-sm font-semibold uppercase tracking-wider text-lime-400">My learning</p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          Wishlist
        </h1>
        <p className="mt-3 text-lg text-foreground/60">Courses you&apos;ve saved for later.</p>
      </div>

      {!accessToken && <LoadingState label="Loading your wishlist…" />}

      {accessToken && items.length === 0 && (
        <div className="mt-16 flex flex-col items-center rounded-2xl border border-dashed border-border-strong py-20 text-center">
          <HeartOff className="h-10 w-10 text-foreground/30" />
          <p className="mt-4 text-sm text-foreground/50">Nothing wishlisted yet.</p>
          <Link href="/courses" className="mt-4 text-sm font-medium text-teal-400 hover:underline">
            Browse courses
          </Link>
        </div>
      )}

      {accessToken && items.length > 0 && (
        <div className="mt-10 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((item) => (
            <div
              key={item.course.id}
              className="flex flex-col rounded-2xl border border-border bg-surface p-5"
            >
              <Link href={`/courses/${item.course.id}`} className="group flex-1">
                <h3 className="text-base font-semibold text-foreground group-hover:text-teal-600 dark:group-hover:text-teal-300">
                  {item.course.title}
                </h3>
                <p className="mt-1.5 line-clamp-2 text-sm text-foreground/60">
                  {item.course.summary}
                </p>
              </Link>
              <div className="mt-4 flex items-center justify-between border-t border-border pt-4">
                <span className="text-xs text-foreground/50">
                  Added {new Date(item.added_at).toLocaleDateString()}
                </span>
                <button
                  type="button"
                  onClick={() => toggle(item.course)}
                  aria-label="Remove from wishlist"
                  className="rounded-full p-1.5 text-rose-400 transition-colors hover:bg-rose-500/10"
                >
                  <Heart className="h-4 w-4 fill-current" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
