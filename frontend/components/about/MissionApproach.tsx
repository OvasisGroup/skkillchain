import { Compass, Hammer } from "lucide-react";

const APPROACH_POINTS = [
  "Courses are interactive and applied, not just theoretical.",
  "Students build real blockchain and AI projects.",
  "Instructors are working professionals, developers, and mentors.",
  "Learners can join bootcamps, participate in hackathons, and get hired through our talent network.",
];

export function MissionApproach() {
  return (
    <section className="mx-auto max-w-7xl px-6 py-24">
      <div className="mx-auto max-w-2xl text-center">
        <p className="text-sm font-semibold uppercase tracking-wider text-lime-400">
          About SkillChain
        </p>
        <h2 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          Empowering the next generation of blockchain and AI developers
        </h2>
      </div>

      <div className="mx-auto mt-16 grid max-w-2xl grid-cols-1 gap-10 lg:max-w-none lg:grid-cols-2">
        <div className="rounded-2xl border border-border bg-surface p-8">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-teal-500/10 text-teal-400">
            <Compass className="h-5 w-5" strokeWidth={2} />
          </div>
          <h3 className="mt-5 text-lg font-semibold text-foreground">Our mission</h3>
          <p className="mt-3 text-sm leading-7 text-foreground/60">
            To make blockchain and AI education accessible, practical, and rewarding for everyone
            — especially African youth. We aim to close the skills gap by enabling learners to
            build real applications, showcase their talent, and access global opportunities
            through community-driven learning.
          </p>
        </div>

        <div className="rounded-2xl border border-border bg-surface p-8">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-teal-500/10 text-teal-400">
            <Hammer className="h-5 w-5" strokeWidth={2} />
          </div>
          <h3 className="mt-5 text-lg font-semibold text-foreground">Our approach</h3>
          <p className="mt-3 text-sm leading-7 text-foreground/60">
            We believe in learning by doing.
          </p>
          <ul className="mt-4 space-y-3">
            {APPROACH_POINTS.map((point) => (
              <li key={point} className="flex items-start gap-2.5 text-sm text-foreground/70">
                <span className="mt-1.5 h-1.5 w-1.5 flex-none rounded-full bg-teal-400" />
                {point}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
