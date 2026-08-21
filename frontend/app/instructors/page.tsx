import { AlertTriangle, Users } from "lucide-react";
import { InstructorCard } from "@/components/InstructorCard";
import { listInstructors } from "@/lib/api/instructors";
import type { InstructorSummary } from "@/lib/api/types";
import { Reveal } from "@/components/animation/Reveal";

export const metadata = {
  title: "Instructors",
  description:
    "Meet the expert instructors teaching blockchain and AI courses on SkillChain — browse profiles, published courses, and specializations.",
  alternates: { canonical: "/instructors" },
};

export default async function InstructorsPage() {
  let instructors: InstructorSummary[] = [];
  let loadError: string | null = null;

  try {
    instructors = await listInstructors();
  } catch {
    loadError =
      "We couldn't reach the instructor directory right now. Make sure the SkillChain API is running.";
  }

  return (
    <div className="mx-auto max-w-7xl px-6 py-16">
      <Reveal className="max-w-2xl">
        <p className="text-sm font-semibold uppercase tracking-wider text-lime-400">
          Instructors
        </p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          Meet our instructors
        </h1>
        <p className="mt-3 text-lg text-foreground/60">
          Working practitioners teaching the skills they use every day.
        </p>
      </Reveal>

      {loadError && (
        <div className="mt-10 flex items-start gap-3 rounded-xl border border-amber-500/20 bg-amber-500/10 p-4 text-sm text-amber-400">
          <AlertTriangle className="mt-0.5 h-5 w-5 flex-none" />
          <span>{loadError}</span>
        </div>
      )}

      {!loadError && instructors.length === 0 && (
        <div className="mt-16 flex flex-col items-center rounded-2xl border border-dashed border-border-strong py-20 text-center">
          <Users className="h-10 w-10 text-foreground/30" />
          <p className="mt-4 text-sm text-foreground/50">
            No instructors yet — check back soon.
          </p>
        </div>
      )}

      {instructors.length > 0 && (
        <Reveal
          className="mt-12 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3"
          stagger={0.08}
        >
          {instructors.map((instructor) => (
            <InstructorCard key={instructor.id} instructor={instructor} />
          ))}
        </Reveal>
      )}
    </div>
  );
}
