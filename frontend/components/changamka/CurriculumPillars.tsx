import { Flag, Scale, Sparkles, Target } from "lucide-react";
import { Reveal } from "@/components/animation/Reveal";

const MODULES = [
  {
    number: "01",
    icon: Target,
    title: "Understanding AI",
    tagline: "Build your AI foundation.",
    description:
      "Learn what artificial intelligence is, what it isn't, and how it is already being used in everyday Kenyan life.",
    topics: ["What AI is and isn't", "AI in everyday life", "Common AI myths", "Identify AI around you"],
    challenge: "Find 10 ways AI is already part of your world.",
  },
  {
    number: "02",
    icon: Sparkles,
    title: "The AI Toolkit",
    tagline: "Turn AI into your everyday productivity partner.",
    description:
      "Get introduced to tools such as ChatGPT, Claude and Gemini and learn how to communicate effectively with AI.",
    topics: ["Research", "Assignments", "Brainstorming", "Planning", "Budgeting", "Problem solving"],
    challenge: "Create your first effective AI prompt to solve a real-world problem.",
  },
  {
    number: "03",
    icon: Flag,
    title: "AI for Future Readiness",
    tagline: "Prepare for the world of work.",
    description:
      "AI is changing the skills employers look for. Learn how to use AI to strengthen your career preparation.",
    topics: [
      "AI-assisted CV",
      "Cover letters",
      "Exam preparation",
      "Study techniques",
      "Employer AI skills",
      "Career planning",
    ],
    challenge: "Create your own AI-assisted career roadmap.",
  },
  {
    number: "04",
    icon: Scale,
    title: "Ethical AI & Digital Citizenship",
    tagline: "Use AI responsibly.",
    description:
      "AI is powerful — but knowing how to use it responsibly is just as important as knowing how to use it.",
    topics: [
      "AI bias and fairness",
      "How AI makes mistakes",
      "Data privacy",
      "Kenya Data Protection Act, 2019",
      "Responsible AI use",
      "Your human advantage",
    ],
    challenge: "Capstone: develop an AI-powered solution to a community challenge.",
  },
];

export function CurriculumPillars() {
  return (
    <section id="curriculum" className="mx-auto max-w-7xl scroll-mt-20 px-6 py-24">
      <Reveal className="mx-auto max-w-2xl text-center">
        <p className="text-sm font-semibold uppercase tracking-wider text-teal-400">
          What you&apos;ll learn
        </p>
        <h2 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          Four pillars. One AI-ready future.
        </h2>
      </Reveal>

      <Reveal className="mx-auto mt-16 grid max-w-2xl grid-cols-1 gap-6 lg:max-w-none lg:grid-cols-2" stagger={0.1}>
        {MODULES.map(({ number, icon: Icon, title, tagline, description, topics, challenge }) => (
          <div key={number} className="flex flex-col rounded-2xl border border-border bg-surface p-8">
            <div className="flex items-center gap-4">
              <span className="font-display text-3xl font-semibold text-teal-400/40">
                {number}
              </span>
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-teal-500/10 text-teal-400">
                <Icon className="h-5 w-5" strokeWidth={2} />
              </div>
            </div>
            <h3 className="mt-4 text-lg font-semibold text-foreground">{title}</h3>
            <p className="mt-1 text-sm font-medium text-foreground/50">{tagline}</p>
            <p className="mt-3 text-sm leading-6 text-foreground/60">{description}</p>

            <div className="mt-5 flex flex-wrap gap-2">
              {topics.map((topic) => (
                <span
                  key={topic}
                  className="rounded-full border border-border-strong bg-background px-3 py-1 text-xs font-medium text-foreground/70"
                >
                  {topic}
                </span>
              ))}
            </div>

            <div className="mt-6 flex-1 rounded-xl border border-dashed border-teal-400/30 bg-teal-400/5 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-teal-400">
                Practical challenge
              </p>
              <p className="mt-1.5 text-sm text-foreground/70">{challenge}</p>
            </div>
          </div>
        ))}
      </Reveal>
    </section>
  );
}
