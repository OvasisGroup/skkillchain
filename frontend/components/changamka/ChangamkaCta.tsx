import { ArrowRight } from "lucide-react";
import Link from "next/link";
import { Reveal } from "@/components/animation/Reveal";

const TAGS = ["Ksh 2,000", "20 Hours", "UK Certified", "No Coding Required"];

export function ChangamkaCta() {
  return (
    <section className="mx-auto max-w-7xl px-6 py-24">
      <Reveal
        y={32}
        className="relative overflow-hidden rounded-3xl bg-teal-600 px-8 py-16 text-center shadow-2xl shadow-teal-900/30 sm:px-16"
      >
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 opacity-20 [background:radial-gradient(circle_at_20%_20%,white,transparent_35%)]"
        />
        <p className="relative text-sm font-semibold uppercase tracking-wider text-emerald-50/70">
          Ready to Changamka?
        </p>
        <h2 className="relative mx-auto mt-3 max-w-2xl text-3xl font-semibold tracking-tight text-white sm:text-4xl">
          Wake up to AI. Build your skills. Start your future.
        </h2>
        <p className="relative mx-auto mt-4 max-w-xl text-lg text-emerald-50/80">
          Don&apos;t wait for AI to change your future — learn how to use it.
        </p>

        <div className="relative mt-8 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-sm font-semibold text-emerald-50/80">
          {TAGS.map((tag, i) => (
            <span key={tag} className="flex items-center gap-6">
              {tag}
              {i < TAGS.length - 1 && <span className="text-emerald-50/40">•</span>}
            </span>
          ))}
        </div>

        <div className="relative mt-10 flex flex-wrap items-center justify-center gap-4">
          <Link
            href="/register"
            className="group inline-flex items-center gap-2 rounded-full bg-white px-6 py-3.5 text-sm font-semibold text-emerald-950 shadow-lg transition-transform hover:scale-[1.02]"
          >
            Start learning now
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
          </Link>
        </div>

        <p className="relative mt-10 border-t border-white/15 pt-6 text-xs text-emerald-50/60">
          A strategic partnership initiative by MUIAA Ltd &amp; Otermans Institute UK
        </p>
      </Reveal>
    </section>
  );
}
