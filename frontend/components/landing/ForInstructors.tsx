import { ArrowRight, CheckCircle2 } from "lucide-react";
import Link from "next/link";
import { Reveal } from "@/components/animation/Reveal";

const POINTS = [
  "Author courses with sections, lessons, quizzes, assignments, and coding exercises",
  "Run coupons and promotions to grow enrollment",
  "Schedule live sessions with automatic Zoom/Google Meet integration",
  "Get paid automatically — earnings land in your instructor wallet after every sale",
];

export function ForInstructors() {
  return (
    <section id="for-instructors" className="mx-auto max-w-7xl px-6 py-24">
      <div className="grid grid-cols-1 items-center gap-12 lg:grid-cols-2">
        <Reveal>
          <p className="text-sm font-semibold uppercase tracking-wider text-lime-400">
            For instructors
          </p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            Teach what you know. <span className="text-teal-400">Get paid for it.</span>
          </h2>
          <p className="mt-4 text-lg text-foreground/60">
            Apply to become an instructor and turn your expertise into a course thousands of
            people can learn from.
          </p>

          <ul className="mt-8 space-y-4">
            {POINTS.map((point) => (
              <li key={point} className="flex items-start gap-3">
                <CheckCircle2 className="mt-0.5 h-5 w-5 flex-none text-teal-400" />
                <span className="text-sm text-foreground/70">{point}</span>
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
        </Reveal>

        <Reveal
          className="rounded-2xl border border-border bg-foreground/[0.03] p-8"
          delay={0.15}
        >
          <div className="space-y-4">
            <div className="flex items-center justify-between rounded-xl border border-border bg-surface p-5">
              <span className="text-sm font-medium text-foreground/50">
                This month&apos;s earnings
              </span>
              <span className="text-2xl font-semibold text-foreground">
                $1,240.00
              </span>
            </div>
            <div className="flex items-center justify-between rounded-xl border border-border bg-surface p-5">
              <span className="text-sm font-medium text-foreground/50">
                Active enrollments
              </span>
              <span className="text-2xl font-semibold text-foreground">312</span>
            </div>
            <div className="flex items-center justify-between rounded-xl border border-border bg-surface p-5">
              <span className="text-sm font-medium text-foreground/50">
                Average rating
              </span>
              <span className="text-2xl font-semibold text-foreground">4.8 ★</span>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
