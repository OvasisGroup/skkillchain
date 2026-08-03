"use client";

import { Search, X } from "lucide-react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import type { Category } from "@/lib/api/types";

const DIFFICULTIES = [
  { value: "", label: "All levels" },
  { value: "beginner", label: "Beginner" },
  { value: "intermediate", label: "Intermediate" },
  { value: "advanced", label: "Advanced" },
];

const PRICES = [
  { value: "", label: "All prices" },
  { value: "true", label: "Free" },
  { value: "false", label: "Paid" },
];

// Course.language is a freeform ISO code with no server-side enum, so this
// is a curated shortlist rather than something derived from the API — it
// covers what a catalog is likely to offer, not just what's seeded today.
const LANGUAGES = [
  { value: "", label: "All languages" },
  { value: "en", label: "English" },
  { value: "es", label: "Spanish" },
  { value: "fr", label: "French" },
  { value: "de", label: "German" },
  { value: "pt", label: "Portuguese" },
  { value: "hi", label: "Hindi" },
  { value: "zh", label: "Mandarin" },
  { value: "ar", label: "Arabic" },
];

const SELECT_CLASS =
  "rounded-lg border border-border-strong bg-surface px-3 py-2 text-sm text-foreground focus:border-teal-400 focus:outline-none";

export function CourseFilters({ categories }: { categories: Category[] }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const [search, setSearch] = useState(searchParams.get("q") ?? "");

  function updateParam(key: string, value: string) {
    const next = new URLSearchParams(searchParams.toString());
    if (value) next.set(key, value);
    else next.delete(key);
    router.push(`${pathname}?${next.toString()}`);
  }

  // Debounced so every keystroke doesn't trigger a navigation/refetch.
  useEffect(() => {
    const current = searchParams.get("q") ?? "";
    if (search === current) return;
    const timeout = setTimeout(() => updateParam("q", search), 400);
    return () => clearTimeout(timeout);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search]);

  const hasActiveFilters =
    searchParams.get("category") ||
    searchParams.get("difficulty") ||
    searchParams.get("language") ||
    searchParams.get("is_free") ||
    searchParams.get("q");

  return (
    <div className="mt-10 flex flex-wrap items-center gap-3">
      <div className="relative flex-1 basis-64">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground/40" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search courses…"
          className={`w-full py-2 pl-9 pr-3 ${SELECT_CLASS}`}
        />
      </div>

      <select
        value={searchParams.get("category") ?? ""}
        onChange={(e) => updateParam("category", e.target.value)}
        className={SELECT_CLASS}
      >
        <option value="">All categories</option>
        {categories.map((category) => (
          <option key={category.id} value={category.slug}>
            {category.name}
          </option>
        ))}
      </select>

      <select
        value={searchParams.get("difficulty") ?? ""}
        onChange={(e) => updateParam("difficulty", e.target.value)}
        className={SELECT_CLASS}
      >
        {DIFFICULTIES.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>

      <select
        value={searchParams.get("language") ?? ""}
        onChange={(e) => updateParam("language", e.target.value)}
        className={SELECT_CLASS}
      >
        {LANGUAGES.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>

      <select
        value={searchParams.get("is_free") ?? ""}
        onChange={(e) => updateParam("is_free", e.target.value)}
        className={SELECT_CLASS}
      >
        {PRICES.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>

      {hasActiveFilters && (
        <button
          type="button"
          onClick={() => {
            setSearch("");
            router.push(pathname);
          }}
          className="flex items-center gap-1 text-sm font-medium text-foreground/60 hover:text-foreground"
        >
          <X className="h-3.5 w-3.5" /> Clear filters
        </button>
      )}
    </div>
  );
}
