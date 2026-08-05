import { AlertTriangle, BookX } from "lucide-react";
import { Suspense } from "react";
import { CourseCard } from "@/components/CourseCard";
import { CourseFilters } from "@/components/CourseFilters";
import { listCategories, listCourses } from "@/lib/api/courses";
import type { Category, Course } from "@/lib/api/types";
import { Reveal } from "@/components/animation/Reveal";

export const metadata = {
  title: "Browse courses",
  description:
    "Explore SkillChain's catalog of blockchain and AI courses — filter by category, language, and difficulty to find your next course.",
  alternates: { canonical: "/courses" },
};

export default async function CoursesPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = await searchParams;
  const category = typeof params.category === "string" ? params.category : undefined;
  const language = typeof params.language === "string" ? params.language : undefined;
  const difficulty = typeof params.difficulty === "string" ? params.difficulty : undefined;
  const q = typeof params.q === "string" ? params.q : undefined;
  const is_free = typeof params.is_free === "string" ? params.is_free === "true" : undefined;
  const hasFilters = Boolean(category || language || difficulty || q || params.is_free);

  let courses: Course[] = [];
  let categories: Category[] = [];
  let loadError: string | null = null;

  try {
    const [page, categoryList] = await Promise.all([
      listCourses({ category, language, difficulty, q, is_free }),
      listCategories(),
    ]);
    courses = page.results;
    categories = categoryList;
  } catch {
    loadError =
      "We couldn't reach the course catalog right now. Make sure the SkillChain API is running.";
  }

  return (
    <div className="mx-auto max-w-7xl px-6 py-16">
      <Reveal className="max-w-2xl">
        <p className="text-sm font-semibold uppercase tracking-wider text-lime-400">Catalog</p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          Browse courses
        </h1>
        <p className="mt-3 text-lg text-foreground/60">
          Live, published courses served straight from the SkillChain API.
        </p>
      </Reveal>

      <Suspense>
        <CourseFilters categories={categories} />
      </Suspense>

      {loadError && (
        <div className="mt-10 flex items-start gap-3 rounded-xl border border-amber-500/20 bg-amber-500/10 p-4 text-sm text-amber-400">
          <AlertTriangle className="mt-0.5 h-5 w-5 flex-none" />
          <span>{loadError}</span>
        </div>
      )}

      {!loadError && courses.length === 0 && (
        <div className="mt-16 flex flex-col items-center rounded-2xl border border-dashed border-border-strong py-20 text-center">
          <BookX className="h-10 w-10 text-foreground/30" />
          <p className="mt-4 text-sm text-foreground/50">
            {hasFilters
              ? "No courses match these filters — try broadening your search."
              : "No published courses yet — check back soon."}
          </p>
        </div>
      )}

      {courses.length > 0 && (
        <div className="mt-8 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {courses.map((course) => (
            <CourseCard key={course.id} course={course} />
          ))}
        </div>
      )}
    </div>
  );
}
