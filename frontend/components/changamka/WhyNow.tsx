import { Briefcase, GraduationCap, Lightbulb, Search } from "lucide-react";
import { Reveal } from "@/components/animation/Reveal";

const SIGNALS = [
  { icon: GraduationCap, label: "How students study" },
  { icon: Briefcase, label: "How businesses operate" },
  { icon: Search, label: "How people find jobs" },
  { icon: Lightbulb, label: "How we solve everyday problems" },
];

export function WhyNow() {
  return (
    <section className="mx-auto max-w-7xl px-6 py-24">
      <div className="grid grid-cols-1 items-center gap-12 lg:grid-cols-2">
        <Reveal>
          <p className="text-sm font-semibold uppercase tracking-wider text-teal-400">
            AI is already here
          </p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            Are you ready for what&apos;s next?
          </h2>
          <p className="mt-5 text-base leading-7 text-foreground/60">
            AI isn&apos;t just something for programmers or tech companies. It is already
            changing how students study, how businesses operate, how people find jobs and how we
            solve everyday problems.
          </p>
          <p className="mt-4 text-base leading-7 text-foreground/60">
            Yet AI literacy isn&apos;t part of the standard curriculum, while students are
            increasingly expected to understand and use AI responsibly.{" "}
            <span className="font-semibold text-foreground">Changamka bridges that gap.</span>
          </p>
          <p className="mt-4 text-base leading-7 text-foreground/60">
            Learn how AI works, how to use today&apos;s most powerful AI tools, how to prepare
            for the future of work — and how to use AI ethically.
          </p>
        </Reveal>

        <Reveal className="grid grid-cols-2 gap-4" stagger={0.1}>
          {SIGNALS.map(({ icon: Icon, label }) => (
            <div
              key={label}
              className="rounded-2xl border border-border bg-surface p-6 transition-colors hover:border-teal-400/30"
            >
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-teal-500/10 text-teal-400">
                <Icon className="h-5 w-5" strokeWidth={2} />
              </div>
              <p className="mt-4 text-sm font-medium text-foreground/80">{label}</p>
            </div>
          ))}
        </Reveal>
      </div>
    </section>
  );
}
