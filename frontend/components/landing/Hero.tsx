import { ArrowRight, PlayCircle } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { Reveal } from "@/components/animation/Reveal";

export function Hero() {
  return (
    <section className="relative overflow-hidden">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 -top-40 -z-10 transform-gpu blur-3xl"
      >
        <div className="mx-auto h-[36rem] w-[72rem] bg-teal-400/20 [clip-path:polygon(74%_44%,100%_61%,97%_26%,85%_0%,80%_2%,72%_32%,60%_62%,32%_35%,2%_46%,0%_68%,32%_100%,60%_75%)]" />
      </div>

      <div className="mx-auto max-w-7xl px-6 pt-20 sm:pt-28 lg:grid lg:grid-cols-2 lg:items-center lg:gap-x-12 lg:pt-32">
        <Reveal className="mx-auto max-w-2xl lg:mx-0" start="top 100%">

          <h2 className="mt-4 text-2xl font-semibold tracking-tight text-foreground sm:text-6xl">
            Your premier platform for{" "}
            <span className="text-teal-400">blockchain and AI education</span> in Africa.
          </h2>

          <p className="mt-6 leading-6 text-foreground/60">
            We empower the next generation of developers, thinkers, and leaders with the tools
            they need to build a better future through hands-on, project-based learning —
            designed for real-world impact.
          </p>

          <div className="mt-10 flex flex-wrap items-center gap-4">
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

          <p className="mt-6 text-sm text-foreground/40">
            Free to register. No credit card required to explore the catalog.
          </p>
        </Reveal>

        <Reveal
          className="mt-16 mr-0 flex justify-center pr-0 lg:mt-0 lg:h-full lg:items-end lg:justify-end lg:self-stretch"
          start="top 100%"
          delay={0.15}
        >
          <Image
            src="/girl_student.png"
            alt="SkillChain platform preview"
            width={785}
            height={1000}
            priority
            className="h-auto w-full max-w-lg object-contain"
          />
        </Reveal>
      </div>
    </section>
  );
}
