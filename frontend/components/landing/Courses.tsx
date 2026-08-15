import { ArrowRight } from "lucide-react";
import Link from "next/link";
import { CourseCard } from "@/components/CourseCard";
import { listCourses } from "@/lib/api/courses";
import { Reveal } from "@/components/animation/Reveal";

const FEATURED_COUNT = 3;

export async function Courses() {
  // Landing content, not a data page — if the API is unreachable or nobody
  // has published a course yet, skip the section entirely rather than show
  // an empty/error block on the homepage.
  const courses = await listCourses()
    .then((page) => page.results)
    .catch(() => []);
  if (courses.length === 0) return null;

  return (
    <section id="courses" className="bg-surface py-24">
      <div className="mx-auto max-w-7xl px-6">
        <Reveal className="mx-auto max-w-4xl text-center">
          <p className="text-sm font-semibold uppercase tracking-wider text-lime-400">
            Catalog
          </p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            Courses to get you building
          </h2>
          <p className="mt-4 text-lg text-foreground/60">
            A sample of what's live right now — browse the full catalog for everything else.
          </p>
        </Reveal>

        <Reveal
          className="mx-auto mt-16 grid max-w-2xl grid-cols-1 gap-6 sm:grid-cols-2 lg:max-w-none lg:grid-cols-3"
          stagger={0.1}
        >
          {courses.slice(0, FEATURED_COUNT).map((course) => (
            <CourseCard key={course.id} course={course} />
          ))}
        </Reveal>

        <div className="mt-10 text-center">
          <Link
            href="/courses"
            className="group inline-flex items-center gap-2 text-sm font-semibold text-teal-400 hover:text-teal-300"
          >
            View all courses
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
          </Link>
        </div>
      </div>
    </section>
  );
}
