import {
  Briefcase,
  Code2,
  GitBranch,
  Globe2,
  Sparkles,
  Trophy,
  Users,
} from "lucide-react";

const DIFFERENTIATORS = [
  {
    icon: Code2,
    title: "Real-world projects",
    description: "Students build working apps and tools, not just watch lecture videos.",
  },
  {
    icon: Trophy,
    title: "Hackathons & bootcamps",
    description: "Government and NGO-backed events that turn learning into a launchpad.",
  },
  {
    icon: Users,
    title: "Mentorship by experts",
    description: "From AI specialists to blockchain engineers, guiding learners directly.",
  },
  {
    icon: Briefcase,
    title: "Job matching portal",
    description: "A talent board connecting graduates with hiring partners.",
  },
  {
    icon: GitBranch,
    title: "Multi-chain curriculum",
    description: "Kadena, Cypherium, Hedera, Cardano, and more — not locked to one chain.",
  },
  {
    icon: Sparkles,
    title: "Developer resource hub",
    description: "GitHub repos, smart contract templates, and API guides ready to build from.",
  },
  {
    icon: Globe2,
    title: "African-focused design",
    description: "Local languages, offline access, and a mobile-first experience.",
  },
];

export function Differentiators() {
  return (
    <section className="bg-surface py-24">
      <div className="mx-auto max-w-7xl px-6">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-semibold uppercase tracking-wider text-lime-400">
            Why SkillChain
          </p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            What makes SkillChain different
          </h2>
        </div>

        <div className="mx-auto mt-16 grid max-w-2xl grid-cols-1 gap-8 sm:grid-cols-2 lg:max-w-none lg:grid-cols-3">
          {DIFFERENTIATORS.map(({ icon: Icon, title, description }) => (
            <div
              key={title}
              className="group rounded-2xl border border-border bg-background p-6 transition-colors hover:border-teal-400/30 hover:bg-surface-hover"
            >
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-teal-500/10 text-teal-400">
                <Icon className="h-5 w-5" strokeWidth={2} />
              </div>
              <h3 className="mt-5 text-base font-semibold text-foreground">{title}</h3>
              <p className="mt-2 text-sm leading-6 text-foreground/60">{description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
