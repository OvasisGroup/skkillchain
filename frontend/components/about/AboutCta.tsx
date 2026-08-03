import { Mail, MapPin, Phone } from "lucide-react";
import Link from "next/link";

export function AboutCta() {
  return (
    <section className="mx-auto max-w-7xl px-6 py-24">
      <div className="relative overflow-hidden rounded-3xl bg-teal-600 px-8 py-16 text-center shadow-2xl shadow-teal-900/30 sm:px-16">
        <h2 className="relative mx-auto max-w-2xl text-3xl font-semibold tracking-tight text-white sm:text-4xl">
          Join us
        </h2>
        <p className="relative mx-auto mt-4 max-w-2xl text-lg text-emerald-50/80">
          SkillChain is Africa&apos;s most intentional blockchain and AI education platform —
          driven by real results, community learning, and job-focused training. If you&apos;re an
          instructor, learner, government partner, NGO, or diaspora ally, join us in building a
          future powered by education and innovation.
        </p>
        <div className="relative mt-10 flex flex-wrap items-center justify-center gap-4">
          <Link
            href="/register"
            className="group inline-flex items-center gap-2 rounded-full bg-white px-6 py-3.5 text-sm font-semibold text-emerald-950 shadow-lg transition-transform hover:scale-[1.02]"
          >
            Get started free
          </Link>
          <Link
            href="/courses"
            className="inline-flex items-center gap-2 rounded-full border border-white/30 px-6 py-3.5 text-sm font-semibold text-white transition-colors hover:bg-white/10"
          >
            Browse courses
          </Link>
        </div>

        <div className="relative mt-12 flex flex-wrap items-center justify-center gap-x-8 gap-y-3 border-t border-white/15 pt-8 text-sm text-emerald-50/70">
          <span className="flex items-center gap-2">
            <MapPin className="h-4 w-4" />
            Nairobi, Kenya
          </span>
          <a
            href="mailto:contact@skillchain.com"
            className="flex items-center gap-2 hover:text-white"
          >
            <Mail className="h-4 w-4" />
            contact@skillchain.com
          </a>
          <a href="tel:+254718540760" className="flex items-center gap-2 hover:text-white">
            <Phone className="h-4 w-4" />
            +254 718 540 760
          </a>
        </div>
      </div>
    </section>
  );
}
