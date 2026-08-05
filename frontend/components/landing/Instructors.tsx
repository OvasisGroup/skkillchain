import { ArrowRight } from "lucide-react";
import Link from "next/link";
import { InstructorCard } from "@/components/InstructorCard";
import { listInstructors } from "@/lib/api/instructors";
import { Reveal } from "@/components/animation/Reveal";

const FEATURED_COUNT = 3;

export async function Instructors() {
  // Landing content, not a data page — if the API is unreachable or nobody
  // has published a course yet, skip the section entirely rather than show
  // an empty/error block on the homepage.
  const instructors = await listInstructors().catch(() => []);
  if (instructors.length === 0) return null;

  return (
    <section id="instructors" className="mx-auto max-w-7xl px-6 py-24">
      <Reveal className="mx-auto max-w-4xl text-center">
        <p className="text-sm font-semibold uppercase tracking-wider text-lime-400">
          Instructors
        </p>
        <h2 className="mt-3 whitespace-nowrap text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          Learn from working practitioners
        </h2>
        <p className="mt-4 whitespace-nowrap text-lg text-foreground/60">
          Every course is taught by someone who does the work, not just talks about it.
        </p>
      </Reveal>

      <Reveal
        className="mx-auto mt-16 grid max-w-2xl grid-cols-1 gap-6 sm:grid-cols-2 lg:max-w-none lg:grid-cols-3"
        stagger={0.1}
      >
        {instructors.slice(0, FEATURED_COUNT).map((instructor) => (
          <InstructorCard key={instructor.id} instructor={instructor} />
        ))}
      </Reveal>

      <div className="mt-10 text-center">
        <Link
          href="/instructors"
          className="group inline-flex items-center gap-2 text-sm font-semibold text-teal-400 hover:text-teal-300"
        >
          View all instructors
          <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
        </Link>
      </div>
    </section>
  );
}
