import { UserRound } from "lucide-react";
import Link from "next/link";
import type { InstructorSummary } from "@/lib/api/types";

function displayName(instructor: InstructorSummary): string {
  const name = `${instructor.profile.first_name} ${instructor.profile.last_name}`.trim();
  return name || instructor.email;
}

export function InstructorCard({ instructor }: { instructor: InstructorSummary }) {
  const name = displayName(instructor);

  return (
    <Link
      href={`/instructors/${instructor.id}`}
      className="group flex flex-col overflow-hidden rounded-2xl border border-border bg-surface shadow-sm transition-all hover:-translate-y-0.5 hover:border-teal-400/50 hover:bg-surface-hover hover:shadow-md"
    >
      <div className="relative flex aspect-video items-center justify-center overflow-hidden bg-teal-500">
        {instructor.profile.avatar ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={instructor.profile.avatar}
            alt=""
            className="absolute inset-0 h-full w-full object-cover"
          />
        ) : (
          <UserRound className="h-12 w-12 text-emerald-950/80" strokeWidth={1.5} />
        )}
      </div>
      <div className="flex flex-1 flex-col p-5">
        <h3 className="text-base font-semibold text-foreground group-hover:text-teal-600 dark:group-hover:text-teal-300">
          {name}
        </h3>
        <p className="mt-1.5 line-clamp-2 flex-1 text-sm text-foreground/60">
          {instructor.profile.bio}
        </p>

        {instructor.categories.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1.5">
            {instructor.categories.map((category) => (
              <span
                key={category.id}
                className="rounded-full bg-surface-hover px-2.5 py-0.5 text-xs font-medium text-foreground/70"
              >
                {category.name}
              </span>
            ))}
          </div>
        )}

        <div className="mt-4 border-t border-border pt-4">
          <span className="text-xs text-foreground/50">
            {instructor.published_course_count}{" "}
            {instructor.published_course_count === 1 ? "course" : "courses"}
          </span>
        </div>
      </div>
    </Link>
  );
}
