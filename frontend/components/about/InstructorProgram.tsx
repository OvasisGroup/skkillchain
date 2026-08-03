import { ArrowRight, CheckCircle2 } from "lucide-react";
import Link from "next/link";

const STEPS = [
  "Apply online with a portfolio or GitHub profile",
  "Pass our vetting and sample module creation",
  "Gain recognition, teach globally, and join our expert network",
];

const ROSTER = [
  "Nairobi County",
  "Computer Aid International",
  "Independent developers from Kenya, the U.S., and the diaspora",
];

export function InstructorProgram() {
  return (
    <section className="bg-surface py-24">
      <div className="mx-auto max-w-7xl px-6">
        <div className="grid grid-cols-1 items-center gap-12 lg:grid-cols-2">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wider text-lime-400">
              Instructor program
            </p>
            <h2 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
              Teach what you know. <span className="text-teal-400">Reach a continent.</span>
            </h2>

            <ul className="mt-8 space-y-4">
              {STEPS.map((step) => (
                <li key={step} className="flex items-start gap-3">
                  <CheckCircle2 className="mt-0.5 h-5 w-5 flex-none text-teal-400" />
                  <span className="text-sm text-foreground/70">{step}</span>
                </li>
              ))}
            </ul>

            <Link
              href="/register"
              className="group mt-10 inline-flex items-center gap-2 rounded-full bg-teal-400 px-6 py-3.5 text-sm font-semibold text-emerald-950 shadow-lg shadow-teal-500/20 transition-opacity hover:opacity-90"
            >
              Apply to teach
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            </Link>
          </div>

          <div className="rounded-2xl border border-border bg-background p-8">
            <p className="text-sm font-semibold text-foreground">
              Our current roster includes mentors from
            </p>
            <ul className="mt-4 space-y-3">
              {ROSTER.map((entry) => (
                <li
                  key={entry}
                  className="rounded-xl border border-border bg-surface p-4 text-sm text-foreground/70"
                >
                  {entry}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
