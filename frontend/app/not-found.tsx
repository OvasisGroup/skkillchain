import { CodeXml, Compass, Home, Search } from "lucide-react";
import Link from "next/link";

export default function NotFound() {
  return (
    <section className="relative flex min-h-[calc(100vh-4rem)] items-center overflow-hidden">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 -top-40 -z-10 transform-gpu blur-3xl"
      >
        <div className="mx-auto h-[36rem] w-[72rem] bg-teal-400/20 [clip-path:polygon(74%_44%,100%_61%,97%_26%,85%_0%,80%_2%,72%_32%,60%_62%,32%_35%,2%_46%,0%_68%,32%_100%,60%_75%)]" />
      </div>

      <div className="mx-auto max-w-2xl px-6 py-24 text-center">
        <span className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-teal-400 text-emerald-950 shadow-lg shadow-teal-500/20">
          <CodeXml className="h-9 w-9" strokeWidth={2.5} />
        </span>

        <p className="mt-8 font-display text-8xl font-semibold tracking-tight text-teal-400 sm:text-9xl">
          404
        </p>

        <h1 className="mt-4 text-2xl font-semibold tracking-tight text-foreground sm:text-4xl">
          This page didn&apos;t make the syllabus.
        </h1>

        <p className="mt-4 text-foreground/60">
          The page you&apos;re looking for may have been moved, renamed, or never existed.
          Let&apos;s get you back on track.
        </p>

        <form
          action="/courses"
          className="mx-auto mt-10 flex max-w-md items-center gap-2 rounded-full border border-border-strong bg-surface p-1.5 pl-4 shadow-sm"
        >
          <Search className="h-4 w-4 shrink-0 text-foreground/40" />
          <input
            type="text"
            name="search"
            placeholder="Search courses..."
            className="w-full bg-transparent text-sm text-foreground placeholder:text-foreground/40 focus:outline-none"
          />
          <button
            type="submit"
            className="shrink-0 rounded-full bg-teal-400 px-4 py-2 text-sm font-semibold text-emerald-950 transition-opacity hover:opacity-90"
          >
            Search
          </button>
        </form>

        <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
          <Link
            href="/"
            className="group inline-flex items-center gap-2 rounded-full bg-teal-400 px-6 py-3.5 text-sm font-semibold text-emerald-950 shadow-lg shadow-teal-500/20 transition-opacity hover:opacity-90"
          >
            <Home className="h-4 w-4" />
            Back to home
          </Link>
          <Link
            href="/courses"
            className="inline-flex items-center gap-2 rounded-full border border-border-strong px-6 py-3.5 text-sm font-semibold text-foreground/90 transition-colors hover:bg-surface"
          >
            <Compass className="h-4 w-4" />
            Browse courses
          </Link>
        </div>
      </div>
    </section>
  );
}
