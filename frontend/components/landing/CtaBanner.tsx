import { ArrowRight } from "lucide-react";
import Link from "next/link";

export function CtaBanner() {
  return (
    <section className="mx-auto max-w-7xl px-6 py-24">
      <div className="relative overflow-hidden rounded-3xl bg-teal-600 px-8 py-16 text-center shadow-2xl shadow-teal-900/30 sm:px-16">
        <h2 className="relative mx-auto max-w-2xl text-3xl font-semibold tracking-tight text-white sm:text-4xl">
          Ready to start learning?
        </h2>
        <p className="relative mx-auto mt-4 max-w-xl text-lg text-emerald-50/80">
          Create your free account and explore the full course catalog in under a minute.
        </p>
        <div className="relative mt-10 flex flex-wrap items-center justify-center gap-4">
          <Link
            href="/register"
            className="group inline-flex items-center gap-2 rounded-full bg-white px-6 py-3.5 text-sm font-semibold text-emerald-950 shadow-lg transition-transform hover:scale-[1.02]"
          >
            Get started free
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
          </Link>
          <Link
            href="/login"
            className="inline-flex items-center gap-2 rounded-full border border-white/30 px-6 py-3.5 text-sm font-semibold text-white transition-colors hover:bg-white/10"
          >
            Log in
          </Link>
        </div>
      </div>
    </section>
  );
}
