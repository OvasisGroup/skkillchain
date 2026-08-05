import { BookOpen, Rocket } from "lucide-react";
import { Reveal } from "@/components/animation/Reveal";

const CORE_CURRICULUM = [
  "Blockchain fundamentals",
  "Smart contract development",
  "DeFi protocols & Web3 tools",
  "AI for developers",
  "Real-world use cases in Africa",
];

const UPCOMING_TRACKS = [
  "Kadena, Cardano, and Cypherium developer programs",
  "Swahili localized learning",
  "Mobile-first, offline-ready courses for rural regions",
];

export function Curriculum() {
  return (
    <section className="mx-auto max-w-7xl px-6 py-24">
      <Reveal className="mx-auto max-w-2xl text-center">
        <p className="text-sm font-semibold uppercase tracking-wider text-lime-400">
          Our courses
        </p>
        <h2 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          Curriculum built for real skills
        </h2>
      </Reveal>

      <Reveal className="mx-auto mt-16 grid max-w-3xl grid-cols-1 gap-8 sm:grid-cols-2" stagger={0.1}>
        <div className="rounded-2xl border border-border bg-surface p-8">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-teal-500/10 text-teal-400">
            <BookOpen className="h-5 w-5" strokeWidth={2} />
          </div>
          <h3 className="mt-5 text-lg font-semibold text-foreground">Core curriculum</h3>
          <ul className="mt-4 space-y-3">
            {CORE_CURRICULUM.map((item) => (
              <li key={item} className="flex items-start gap-2.5 text-sm text-foreground/70">
                <span className="mt-1.5 h-1.5 w-1.5 flex-none rounded-full bg-teal-400" />
                {item}
              </li>
            ))}
          </ul>
        </div>

        <div className="rounded-2xl border border-border bg-surface p-8">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-lime-500/10 text-lime-500">
            <Rocket className="h-5 w-5" strokeWidth={2} />
          </div>
          <h3 className="mt-5 text-lg font-semibold text-foreground">Upcoming tracks</h3>
          <ul className="mt-4 space-y-3">
            {UPCOMING_TRACKS.map((item) => (
              <li key={item} className="flex items-start gap-2.5 text-sm text-foreground/70">
                <span className="mt-1.5 h-1.5 w-1.5 flex-none rounded-full bg-lime-400" />
                {item}
              </li>
            ))}
          </ul>
        </div>
      </Reveal>
    </section>
  );
}
