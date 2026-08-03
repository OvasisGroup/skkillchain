"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { addToWishlist, listWishlist, removeFromWishlist } from "@/lib/api/enrollments";
import type { Course, CourseSummary, WishlistItem } from "@/lib/api/types";
import { useAuth } from "@/lib/auth/AuthContext";

const EMPTY_ITEMS: WishlistItem[] = [];

interface WishlistContextValue {
  items: WishlistItem[];
  courseIds: Set<string>;
  toggle: (course: Course | CourseSummary) => Promise<void>;
}

const WishlistContext = createContext<WishlistContextValue | null>(null);

export function WishlistProvider({ children }: { children: React.ReactNode }) {
  const { accessToken } = useAuth();
  const [items, setItems] = useState<WishlistItem[]>([]);

  useEffect(() => {
    if (!accessToken) return;
    let cancelled = false;
    listWishlist(accessToken)
      .then((data) => {
        if (!cancelled) setItems(data);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [accessToken]);

  const toggle = useCallback(
    async (course: Course | CourseSummary) => {
      if (!accessToken) return;
      const inWishlist = items.some((item) => item.course.id === course.id);
      if (inWishlist) {
        setItems((prev) => prev.filter((item) => item.course.id !== course.id));
        await removeFromWishlist(course.id, accessToken).catch(() => {
          setItems((prev) => [...prev, { course, added_at: new Date().toISOString() }]);
        });
      } else {
        setItems((prev) => [...prev, { course, added_at: new Date().toISOString() }]);
        await addToWishlist(course.id, accessToken).catch(() => {
          setItems((prev) => prev.filter((item) => item.course.id !== course.id));
        });
      }
    },
    [accessToken, items]
  );

  // Derived rather than reset via an effect, so a logout clears the visible
  // wishlist on the very next render instead of leaving stale items on
  // screen for one paint (and never leaking between accounts on the same
  // browser).
  const visibleItems = accessToken ? items : EMPTY_ITEMS;
  const courseIds = useMemo(() => new Set(visibleItems.map((item) => item.course.id)), [visibleItems]);

  const value = useMemo<WishlistContextValue>(
    () => ({ items: visibleItems, courseIds, toggle }),
    [visibleItems, courseIds, toggle]
  );

  return <WishlistContext.Provider value={value}>{children}</WishlistContext.Provider>;
}

export function useWishlist(): WishlistContextValue {
  const context = useContext(WishlistContext);
  if (!context) throw new Error("useWishlist must be used within a WishlistProvider");
  return context;
}
