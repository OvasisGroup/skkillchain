import { Compass, Target, Zap } from "lucide-react";
import { Reveal } from "@/components/animation/Reveal";

const PILLARS = [
  {
    icon: Compass,
    title: "Be Alert",
    description:
      "Awaken to the possibilities of artificial intelligence and understand how AI is already transforming your world.",
  },
  {
    icon: Zap,
    title: "Be Agile",
    description:
      "Develop the skills to adapt as technology and the future of work continue to evolve.",
  },
  {
    icon: Target,
    title: "Be Proactive",
    description:
      "Take control of your digital future and start building the skills employers increasingly value.",
  },
];

export function MindsetPillars() {
  return (
    <section className="bg-surface py-24">
      <div className="mx-auto max-w-7xl px-6">
        <Reveal className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-semibold uppercase tracking-wider text-teal-400">
            What is Changamka?
          </p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            Be Alert. Be Agile. Be Proactive.
          </h2>
          <p className="mt-4 text-base leading-7 text-foreground/60">
            <span className="font-semibold text-foreground">Changamka</span> means &ldquo;be
            alert.&rdquo; It represents a mindset for a generation growing up in an AI-powered
            world.
          </p>
        </Reveal>

        <Reveal
          className="mx-auto mt-16 grid max-w-2xl grid-cols-1 gap-8 lg:max-w-none lg:grid-cols-3"
          stagger={0.1}
        >
          {PILLARS.map(({ icon: Icon, title, description }) => (
            <div
              key={title}
              className="rounded-2xl border border-border bg-background p-8 text-center"
            >
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-teal-400 text-emerald-950 shadow-lg shadow-teal-500/20">
                <Icon className="h-6 w-6" strokeWidth={2} />
              </div>
              <h3 className="mt-5 text-lg font-semibold text-foreground">{title}</h3>
              <p className="mt-3 text-sm leading-6 text-foreground/60">{description}</p>
            </div>
          ))}
        </Reveal>
      </div>
    </section>
  );
}
