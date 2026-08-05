import {
  Award,
  Code2,
  MessagesSquare,
  Sparkles,
  Video,
  Wallet,
} from "lucide-react";
import { Reveal } from "@/components/animation/Reveal";

const FEATURES = [
  {
    icon: Code2,
    title: "Learn by doing",
    description:
      "Quizzes, graded assignments, and judged coding exercises with instant feedback — not just video playback.",
  },
  {
    icon: Video,
    title: "Live instructor sessions",
    description:
      "Join scheduled classes over Zoom or Google Meet, register in one click, and catch the recording if you miss it.",
  },
  {
    icon: Sparkles,
    title: "AI-powered tutor",
    description:
      "Ask questions about any lesson, get AI-generated summaries and flashcards, and grade assignments faster with AI-suggested feedback.",
  },
  {
    icon: MessagesSquare,
    title: "Community & discussions",
    description:
      "Real-time messaging, course discussion threads, and verified reviews from students who actually completed the course.",
  },
  {
    icon: Award,
    title: "Verifiable certificates",
    description:
      "Every completed course issues a certificate with a public verification link — proof employers can actually check.",
  },
  {
    icon: Wallet,
    title: "Built for instructors",
    description:
      "Author courses, run coupons and promotions, and get paid automatically through instructor payouts and wallets.",
  },
];

export function Features() {
  return (
    <section id="features" className="mx-auto max-w-7xl px-6 py-24">
      <Reveal className="mx-auto max-w-4xl text-center">
        <p className="text-sm font-semibold uppercase tracking-wider text-lime-400">
          Platform
        </p>
        <h2 className="mt-3 whitespace-nowrap text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          Everything a modern learning platform needs
        </h2>
        <p className="mt-4 whitespace-nowrap text-lg text-foreground/60">
          One account, one platform — from your first lesson to a certificate you can share.
        </p>
      </Reveal>

      <Reveal
        className="mx-auto mt-16 grid max-w-2xl grid-cols-1 gap-8 sm:grid-cols-2 lg:max-w-none lg:grid-cols-3"
        stagger={0.1}
      >
        {FEATURES.map(({ icon: Icon, title, description }) => (
          <div
            key={title}
            className="group rounded-2xl border border-border bg-surface p-6 transition-colors hover:border-teal-400/30 hover:bg-surface-hover"
          >
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-teal-500/10 text-teal-400">
              <Icon className="h-5 w-5" strokeWidth={2} />
            </div>
            <h3 className="mt-5 text-base font-semibold text-foreground">
              {title}
            </h3>
            <p className="mt-2 text-sm leading-6 text-foreground/60">
              {description}
            </p>
          </div>
        ))}
      </Reveal>
    </section>
  );
}
