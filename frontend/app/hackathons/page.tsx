import { AlertTriangle, Trophy } from "lucide-react";
import Link from "next/link";
import { HackathonCard } from "@/components/HackathonCard";
import { listHackathons, type HackathonScope } from "@/lib/api/hackathons";
import type { Hackathon } from "@/lib/api/types";
import { Reveal } from "@/components/animation/Reveal";

export const metadata = {
  title: "Hackathons",
  description:
    "Browse SkillChain hackathons — hosted internally or with partner organizations — and register to compete.",
  alternates: { canonical: "/hackathons" },
};

const SCOPES: { value: HackathonScope; label: string }[] = [
  { value: "active", label: "Active" },
  { value: "upcoming", label: "Upcoming" },
  { value: "completed", label: "Completed" },
];

export default async function HackathonsPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = await searchParams;
  const rawScope = typeof params.scope === "string" ? params.scope : "active";
  const scope: HackathonScope = SCOPES.some((s) => s.value === rawScope)
    ? (rawScope as HackathonScope)
    : "active";

  let hackathons: Hackathon[] = [];
  let loadError: string | null = null;

  try {
    const page = await listHackathons({ scope });
    hackathons = page.results;
  } catch {
    loadError = "We couldn't reach the hackathons API right now. Make sure it's running.";
  }

  return (
    <div className="mx-auto max-w-7xl px-6 py-16">
      <Reveal className="max-w-2xl">
        <p className="text-sm font-semibold uppercase tracking-wider text-lime-400">Hackathons</p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          Compete, build, win
        </h1>
        <p className="mt-3 text-lg text-foreground/60">
          Hosted by SkillChain, or in partnership with other organizations — register, submit a
          project, and see who wins.
        </p>
      </Reveal>

      <div className="mt-8 flex flex-wrap gap-2">
        {SCOPES.map((s) => (
          <Link
            key={s.value}
            href={`/hackathons?scope=${s.value}`}
            className={`rounded-full px-4 py-1.5 text-sm font-semibold transition-colors ${
              scope === s.value
                ? "bg-teal-400 text-emerald-950"
                : "border border-border-strong text-foreground/70 hover:bg-surface-hover"
            }`}
          >
            {s.label}
          </Link>
        ))}
      </div>

      {loadError && (
        <div className="mt-10 flex items-start gap-3 rounded-xl border border-amber-500/20 bg-amber-500/10 p-4 text-sm text-amber-400">
          <AlertTriangle className="mt-0.5 h-5 w-5 flex-none" />
          <span>{loadError}</span>
        </div>
      )}

      {!loadError && hackathons.length === 0 && (
        <div className="mt-16 flex flex-col items-center rounded-2xl border border-dashed border-border-strong py-20 text-center">
          <Trophy className="h-10 w-10 text-foreground/30" />
          <p className="mt-4 text-sm text-foreground/50">
            No {scope} hackathons right now — check back soon.
          </p>
        </div>
      )}

      {hackathons.length > 0 && (
        <div className="mt-8 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {hackathons.map((hackathon) => (
            <HackathonCard key={hackathon.id} hackathon={hackathon} />
          ))}
        </div>
      )}
    </div>
  );
}
