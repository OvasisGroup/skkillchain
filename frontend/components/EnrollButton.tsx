"use client";

import { CheckCircle2, Loader2, ShoppingCart } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { enroll, listMyCourses } from "@/lib/api/enrollments";
import { ApiError } from "@/lib/api/client";
import type { Course } from "@/lib/api/types";
import { useAuth } from "@/lib/auth/AuthContext";
import { useCart } from "@/lib/cart/CartContext";

const ALREADY_ENROLLED_MESSAGE = "Already enrolled in this course.";

export function EnrollButton({ course }: { course: Course }) {
  const { isAuthenticated, accessToken } = useAuth();
  const { isInCart, addItem } = useCart();
  const router = useRouter();
  const [status, setStatus] = useState<"idle" | "loading" | "enrolled" | "error">("idle");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken) return;
    let cancelled = false;
    listMyCourses(accessToken)
      .then((page) => {
        if (!cancelled && page.results.some((e) => e.course.id === course.id)) {
          setStatus("enrolled");
        }
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [accessToken, course.id]);

  const isFree = Number(course.price_amount) === 0;

  if (!isAuthenticated) {
    return (
      <Link
        href={`/register?next=${encodeURIComponent(`/courses/${course.id}`)}`}
        className="block w-full rounded-full bg-teal-400 px-6 py-3.5 text-center text-sm font-semibold text-emerald-950 shadow-sm shadow-teal-500/20 transition-opacity hover:opacity-90"
      >
        {isFree
          ? "Sign up to enroll — it's free"
          : `Sign up to buy for ${course.currency} ${course.price_amount}`}
      </Link>
    );
  }

  if (status === "enrolled") {
    return (
      <div className="space-y-2">
        <div className="flex w-full items-center justify-center gap-2 rounded-full bg-emerald-500/10 px-6 py-3.5 text-sm font-semibold text-emerald-400">
          <CheckCircle2 className="h-4 w-4" />
          You&apos;re enrolled
        </div>
        <Link
          href={`/learn/${course.id}`}
          className="block w-full rounded-full bg-teal-400 px-6 py-3.5 text-center text-sm font-semibold text-emerald-950 shadow-sm shadow-teal-500/20 transition-opacity hover:opacity-90"
        >
          Continue learning
        </Link>
      </div>
    );
  }

  if (!isFree) {
    if (isInCart(course.id)) {
      return (
        <Link
          href="/cart"
          className="flex w-full items-center justify-center gap-2 rounded-full bg-teal-400 px-6 py-3.5 text-sm font-semibold text-emerald-950 shadow-sm shadow-teal-500/20 transition-opacity hover:opacity-90"
        >
          <ShoppingCart className="h-4 w-4" />
          In cart — go to checkout
        </Link>
      );
    }

    return (
      <button
        type="button"
        onClick={() => {
          addItem(course);
          router.push("/cart");
        }}
        className="w-full rounded-full bg-teal-400 px-6 py-3.5 text-sm font-semibold text-emerald-950 shadow-sm shadow-teal-500/20 transition-opacity hover:opacity-90"
      >
        Buy for {course.currency} {course.price_amount}
      </button>
    );
  }

  async function handleEnroll() {
    if (!accessToken) return;
    setStatus("loading");
    setError(null);
    try {
      await enroll(course.id, accessToken);
      setStatus("enrolled");
    } catch (err) {
      if (err instanceof ApiError && err.message_.includes(ALREADY_ENROLLED_MESSAGE)) {
        setStatus("enrolled");
        return;
      }
      setError(err instanceof ApiError ? err.message_ : "Something went wrong. Please try again.");
      setStatus("error");
    }
  }

  return (
    <div>
      <button
        type="button"
        onClick={handleEnroll}
        disabled={status === "loading"}
        className="flex w-full items-center justify-center gap-2 rounded-full bg-teal-400 px-6 py-3.5 text-sm font-semibold text-emerald-950 shadow-sm shadow-teal-500/20 transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {status === "loading" && <Loader2 className="h-4 w-4 animate-spin" />}
        {status === "loading" ? "Enrolling…" : "Enroll for free"}
      </button>
      {error && <p className="mt-2 text-center text-xs text-red-400">{error}</p>}
    </div>
  );
}
