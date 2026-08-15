"use client";

import { BookOpen, Check, Heart, ShoppingCart } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth/AuthContext";
import { useCart } from "@/lib/cart/CartContext";
import type { Course } from "@/lib/api/types";
import { displayName } from "@/lib/displayName";
import { useWishlist } from "@/lib/wishlist/WishlistContext";

const DIFFICULTY_STYLES: Record<Course["difficulty"], string> = {
  beginner: "bg-emerald-500/10 text-emerald-400",
  intermediate: "bg-amber-500/10 text-amber-400",
  advanced: "bg-rose-500/10 text-rose-400",
};

export function CourseCard({ course }: { course: Course }) {
  const router = useRouter();
  const { isAuthenticated } = useAuth();
  const { courseIds, toggle } = useWishlist();
  const { isInCart, addItem, removeItem } = useCart();

  const wishlisted = courseIds.has(course.id);
  const inCart = isInCart(course.id);

  function handleWishlistClick(e: React.MouseEvent) {
    e.preventDefault();
    if (!isAuthenticated) {
      router.push("/login");
      return;
    }
    toggle(course);
  }

  function handleCartClick(e: React.MouseEvent) {
    e.preventDefault();
    if (!isAuthenticated) {
      router.push("/login");
      return;
    }
    if (inCart) {
      removeItem(course.id);
    } else {
      addItem(course);
    }
  }

  return (
    <div className="group flex flex-col overflow-hidden rounded-2xl border border-border bg-surface shadow-sm transition-all hover:-translate-y-0.5 hover:border-teal-400/50 hover:bg-surface-hover hover:shadow-md">
      <div className="relative flex aspect-video items-center justify-center overflow-hidden bg-teal-500">
        <Link href={`/courses/${course.id}`} className="absolute inset-0 z-10" aria-label={course.title} />
        {course.cover_image ? (
          <Image
            src={course.cover_image}
            alt=""
            fill
            sizes="(min-width: 1024px) 400px, (min-width: 640px) 50vw, 100vw"
            className="object-cover"
          />
        ) : (
          <BookOpen className="h-10 w-10 text-emerald-950/80" strokeWidth={1.5} />
        )}
        <div className="pointer-events-none absolute right-2.5 top-2.5 z-20 flex gap-1.5">
          <button
            type="button"
            onClick={handleWishlistClick}
            aria-label={wishlisted ? "Remove from wishlist" : "Add to wishlist"}
            aria-pressed={wishlisted}
            className={`pointer-events-auto flex h-8 w-8 items-center justify-center rounded-full shadow-sm transition-colors ${
              wishlisted
                ? "bg-rose-500 text-white"
                : "bg-white/90 text-emerald-950/70 hover:bg-white hover:text-emerald-950"
            }`}
          >
            <Heart className={`h-4 w-4 ${wishlisted ? "fill-current" : ""}`} />
          </button>
          <button
            type="button"
            onClick={handleCartClick}
            aria-label={inCart ? "Remove from cart" : "Add to cart"}
            aria-pressed={inCart}
            className={`pointer-events-auto flex h-8 w-8 items-center justify-center rounded-full shadow-sm transition-colors ${
              inCart
                ? "bg-teal-400 text-emerald-950"
                : "bg-white/90 text-emerald-950/70 hover:bg-white hover:text-emerald-950"
            }`}
          >
            {inCart ? <Check className="h-4 w-4" /> : <ShoppingCart className="h-4 w-4" />}
          </button>
        </div>
      </div>
      <Link href={`/courses/${course.id}`} className="flex flex-1 flex-col p-5">
        <div className="flex items-center gap-2">
          <span
            className={`rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${DIFFICULTY_STYLES[course.difficulty]}`}
          >
            {course.difficulty}
          </span>
          <span className="text-xs uppercase tracking-wide text-foreground/40">{course.language}</span>
        </div>
        <h3 className="mt-3 text-base font-semibold text-foreground group-hover:text-teal-600 dark:group-hover:text-teal-300">
          {course.title}
        </h3>
        <p className="mt-1.5 line-clamp-2 flex-1 text-sm text-foreground/60">
          {course.summary}
        </p>
        <div className="mt-4 flex items-center justify-between border-t border-border pt-4">
          <span className="text-xs text-foreground/50">
            {displayName(course.instructor)}
          </span>
          <span className="text-sm font-semibold text-foreground">
            {course.price_amount === "0.00"
              ? "Free"
              : `${course.currency} ${course.price_amount}`}
          </span>
        </div>
      </Link>
    </div>
  );
}
