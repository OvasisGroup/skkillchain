import { ArrowRight, Sparkles } from "lucide-react";
import Link from "next/link";
import { Reveal } from "@/components/animation/Reveal";

const TRUST_MARKS = ["UK-Certified", "Mobile-First", "Affordable", "Built for Kenya"];

const PRICE_STATS = [
  { value: "Ksh 2,000", label: "One-time fee" },
  { value: "20 Hours", label: "Self-paced" },
  { value: "0", label: "Coding required" },
];

const MODULE_PREVIEW = [
  { label: "Understanding AI", pct: 100 },
  { label: "The AI Toolkit", pct: 100 },
  { label: "AI for Future Readiness", pct: 60 },
  { label: "Ethical AI & Digital Citizenship", pct: 0 },
];

export function ChangamkaHero() {
  return (
    <section className="relative overflow-hidden">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 -top-40 -z-10 transform-gpu blur-3xl"
      >
        <div className="mx-auto h-[36rem] w-[72rem] bg-teal-400/20 [clip-path:polygon(74%_44%,100%_61%,97%_26%,85%_0%,80%_2%,72%_32%,60%_62%,32%_35%,2%_46%,0%_68%,32%_100%,60%_75%)]" />
      </div>

      <div className="mx-auto max-w-7xl px-6 pt-16 sm:pt-24 lg:grid lg:grid-cols-2 lg:items-center lg:gap-x-12">
        <Reveal className="mx-auto max-w-2xl lg:mx-0" start="top 100%">
          <span className="inline-flex items-center gap-2 rounded-full border border-teal-400/30 bg-teal-400/10 px-4 py-1.5 text-xs font-semibold uppercase tracking-wider text-teal-400">
            <Sparkles className="h-3.5 w-3.5" />
            AI literacy for every Kenyan student
          </span>

          <h1 className="mt-6 text-3xl font-semibold tracking-tight text-foreground sm:text-5xl">
            Wake up to AI. <span className="text-teal-400">Start your future today.</span>
          </h1>

          <p className="mt-6 text-lg leading-8 text-foreground/60">
            AI is changing the way we learn, work and build businesses. Changamka gives you the
            practical AI skills you need to stay ahead — a self-paced course built specifically
            for Kenyan students, with internationally recognized UK certification.
          </p>

          <div className="mt-8 flex flex-wrap items-center gap-x-8 gap-y-3">
            {PRICE_STATS.map((stat) => (
              <div key={stat.label}>
                <p className="text-xl font-semibold text-foreground">{stat.value}</p>
                <p className="text-xs font-medium uppercase tracking-wide text-foreground/40">
                  {stat.label}
                </p>
              </div>
            ))}
          </div>

          <div className="mt-10 flex flex-col items-stretch gap-4 sm:flex-row sm:flex-wrap sm:items-center">
            <Link
              href="/register"
              className="group inline-flex w-full items-center justify-center gap-2 rounded-full bg-teal-400 px-6 py-3.5 text-sm font-semibold text-emerald-950 shadow-lg shadow-teal-500/20 transition-opacity hover:opacity-90 sm:w-auto"
            >
              Start learning
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            </Link>
            <Link
              href="#curriculum"
              className="inline-flex w-full items-center justify-center gap-2 rounded-full border border-border-strong px-6 py-3.5 text-sm font-semibold text-foreground/90 transition-colors hover:bg-surface sm:w-auto"
            >
              Explore the course
            </Link>
          </div>

          <div className="mt-8 flex flex-wrap items-center gap-x-6 gap-y-2 text-xs font-medium text-foreground/40">
            {TRUST_MARKS.map((mark, i) => (
              <span key={mark} className="flex items-center gap-6">
                {mark}
                {i < TRUST_MARKS.length - 1 && <span className="text-foreground/20">•</span>}
              </span>
            ))}
          </div>
        </Reveal>

        <Reveal
          className="mt-16 flex justify-center lg:mt-0 lg:justify-end"
          start="top 100%"
          delay={0.15}
        >
          <div className="w-full max-w-sm rounded-3xl border border-border bg-surface p-6 shadow-2xl shadow-teal-900/10">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-2 text-sm font-semibold text-foreground">
                <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-teal-400 text-emerald-950">
                  <Sparkles className="h-4 w-4" strokeWidth={2.5} />
                </span>
                Changamka
              </span>
              <span className="rounded-full bg-lime-400/15 px-2.5 py-1 text-[11px] font-semibold text-lime-500">
                65% complete
              </span>
            </div>

            <div className="mt-6 space-y-4">
              {MODULE_PREVIEW.map((module, i) => (
                <div key={module.label}>
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-medium text-foreground/80">
                      0{i + 1} — {module.label}
                    </span>
                    <span className="text-foreground/40">{module.pct}%</span>
                  </div>
                  <div className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-surface-hover">
                    <div
                      className="h-full rounded-full bg-linear-to-r from-teal-400 to-teal-600"
                      style={{ width: `${module.pct}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-6 rounded-xl border border-dashed border-border-strong p-4 text-xs text-foreground/50">
              Certificate unlocks after all four modules and the capstone challenge.
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
