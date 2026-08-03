"use client";

import { createContext, useCallback, useContext, useMemo, useSyncExternalStore } from "react";
import type { Course } from "@/lib/api/types";

const STORAGE_KEY = "skillchain.cart";
const EMPTY: Course[] = [];

interface CartContextValue {
  items: Course[];
  count: number;
  isInCart: (courseId: string) => boolean;
  addItem: (course: Course) => void;
  removeItem: (courseId: string) => void;
  clear: () => void;
}

const CartContext = createContext<CartContextValue | null>(null);

function readStoredCart(): Course[] {
  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (!raw) return [];
  try {
    return JSON.parse(raw) as Course[];
  } catch {
    return [];
  }
}

// Module-level cache, mirroring ThemeContext's useSyncExternalStore pattern:
// the server always renders an empty cart (no localStorage access), and the
// client swaps in the real persisted cart right after hydration with no
// mismatch, since useSyncExternalStore is built for exactly this handoff.
let cache: Course[] = typeof window !== "undefined" ? readStoredCart() : EMPTY;
const listeners = new Set<() => void>();

function subscribe(callback: () => void) {
  listeners.add(callback);
  return () => listeners.delete(callback);
}

function getSnapshot(): Course[] {
  return cache;
}

function getServerSnapshot(): Course[] {
  return EMPTY;
}

function setCache(next: Course[]) {
  cache = next;
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  listeners.forEach((callback) => callback());
}

export function CartProvider({ children }: { children: React.ReactNode }) {
  const items = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

  const isInCart = useCallback(
    (courseId: string) => items.some((item) => item.id === courseId),
    [items]
  );

  const addItem = useCallback(
    (course: Course) => {
      if (items.some((item) => item.id === course.id)) return;
      setCache([...items, course]);
    },
    [items]
  );

  const removeItem = useCallback(
    (courseId: string) => {
      setCache(items.filter((item) => item.id !== courseId));
    },
    [items]
  );

  const clear = useCallback(() => setCache([]), []);

  const value = useMemo<CartContextValue>(
    () => ({ items, count: items.length, isInCart, addItem, removeItem, clear }),
    [items, isInCart, addItem, removeItem, clear]
  );

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export function useCart(): CartContextValue {
  const context = useContext(CartContext);
  if (!context) throw new Error("useCart must be used within a CartProvider");
  return context;
}
