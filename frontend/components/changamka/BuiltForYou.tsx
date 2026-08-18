import { Award, Ban, Clock, MapPin, Smartphone, Wallet } from "lucide-react";
import { Reveal } from "@/components/animation/Reveal";

const FEATURES = [
  {
    icon: Clock,
    title: "20-Hour Course",
    description: "Learn at your own pace and complete the course around your schedule.",
  },
  {
    icon: Smartphone,
    title: "Mobile-First",
    description: "Designed for learning on your phone with a low-data approach.",
  },
  {
    icon: Ban,
    title: "No Coding Required",
    description: "Understand and use AI without needing a programming background.",
  },
  {
    icon: MapPin,
    title: "Kenyan Context",
    description: "Learn through examples relevant to everyday life in Kenya.",
  },
  {
    icon: Award,
    title: "UK Certification",
    description: "Earn an internationally recognized certification from Otermans Institute UK.",
  },
  {
    icon: Wallet,
    title: "Affordable",
    description: "Complete the full course for just Ksh 2,000.",
  },
];

export function BuiltForYou() {
  return (
    <section className="mx-auto max-w-7xl px-6 py-24">
      <Reveal className="mx-auto max-w-2xl text-center">
        <p className="text-sm font-semibold uppercase tracking-wider text-teal-400">
          Built for the next generation
        </p>
        <h2 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          AI skills without the complexity
        </h2>
        <p className="mt-4 text-base leading-7 text-foreground/60">
          You don&apos;t need to be a programmer. You don&apos;t need expensive equipment. You
          don&apos;t need to spend months studying — Changamka is accessible, practical and
          relevant to Kenyan students.
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
            <h3 className="mt-5 text-base font-semibold text-foreground">{title}</h3>
            <p className="mt-2 text-sm leading-6 text-foreground/60">{description}</p>
          </div>
        ))}
      </Reveal>
    </section>
  );
}
