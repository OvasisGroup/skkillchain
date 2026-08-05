import { Award, Briefcase, Code2 } from "lucide-react";
import { Reveal } from "@/components/animation/Reveal";

const OUTCOMES = [
  {
    icon: Award,
    title: "Certifications",
    description:
      "Verifiable, blockchain-signed certificates (not tied to crypto tokens), plus institutional badges backed by partners. Designed to be resumable, searchable, and employer-friendly.",
  },
  {
    icon: Code2,
    title: "Developer resource center",
    description:
      "Pre-built smart contract libraries, API tutorials for Cypherium, Cardano, and Kadena, starter dApp templates, and real-time feedback as you build.",
  },
  {
    icon: Briefcase,
    title: "Job & talent board",
    description:
      "Startups find certified devs, hackathon winners get recruited, diaspora funders hire locally, and NGOs can request blockchain solutions.",
  },
];

export function Outcomes() {
  return (
    <section className="mx-auto max-w-7xl px-6 py-24">
      <Reveal className="mx-auto max-w-2xl text-center">
        <p className="text-sm font-semibold uppercase tracking-wider text-lime-400">
          From learner to builder
        </p>
        <h2 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          What you walk away with
        </h2>
      </Reveal>

      <Reveal
        className="mx-auto mt-16 grid max-w-2xl grid-cols-1 gap-8 lg:max-w-none lg:grid-cols-3"
        stagger={0.1}
      >
        {OUTCOMES.map(({ icon: Icon, title, description }) => (
          <div key={title} className="rounded-2xl border border-border bg-surface p-8">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-teal-500/10 text-teal-400">
              <Icon className="h-5 w-5" strokeWidth={2} />
            </div>
            <h3 className="mt-5 text-lg font-semibold text-foreground">{title}</h3>
            <p className="mt-3 text-sm leading-6 text-foreground/60">{description}</p>
          </div>
        ))}
      </Reveal>
    </section>
  );
}
