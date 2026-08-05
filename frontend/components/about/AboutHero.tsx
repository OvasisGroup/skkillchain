import { ArrowRight, PlayCircle } from "lucide-react";
import Link from "next/link";
import { Reveal } from "@/components/animation/Reveal";

export function AboutHero() {
  return (
    <section className="relative overflow-hidden">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 -top-40 -z-10 transform-gpu blur-3xl"
      >
        <div className="mx-auto h-[36rem] w-[72rem] bg-teal-400/20 [clip-path:polygon(74%_44%,100%_61%,97%_26%,85%_0%,80%_2%,72%_32%,60%_62%,32%_35%,2%_46%,0%_68%,32%_100%,60%_75%)]" />
      </div>

      <Reveal className="mx-auto max-w-4xl px-6 pt-20 text-center sm:pt-28">
        <p className="text-sm font-semibold uppercase tracking-wider text-lime-400">About us</p>
        <h1 className="mt-4 text-3xl font-semibold tracking-tight text-foreground sm:text-5xl">
          The premier platform for{" "}
          <span className="text-teal-400">blockchain and AI education</span> and course creation
        </h1>
        <p className="mx-auto mt-6 max-w-2xl text-lg leading-8 text-foreground/60">
          SkillChain empowers the next generation of developers, thinkers, and leaders with the
          tools they need to build a better future through hands-on, project-based learning —
          designed for real-world impact.
        </p>

        <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
          <Link
            href="/register"
            className="group inline-flex items-center gap-2 rounded-full bg-teal-400 px-6 py-3.5 text-sm font-semibold text-emerald-950 shadow-lg shadow-teal-500/20 transition-opacity hover:opacity-90"
          >
            Get started free
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
          </Link>
          <Link
            href="/courses"
            className="inline-flex items-center gap-2 rounded-full border border-border-strong px-6 py-3.5 text-sm font-semibold text-foreground/90 transition-colors hover:bg-surface"
          >
            <PlayCircle className="h-4 w-4" />
            Browse courses
          </Link>
        </div>
      </Reveal>
    </section>
  );
}
