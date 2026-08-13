import { AlertTriangle, Trophy } from "lucide-react";
import Link from "next/link";
import { HackathonCard } from "@/components/HackathonCard";
import { PreviousHackathonCard } from "@/components/hackathons/PreviousHackathonCard";
import { API_BASE_URL, apiFetch } from "@/lib/api/client";
import { getHackathon, listHackathons, type HackathonScope } from "@/lib/api/hackathons";
import type { CursorPage, Hackathon, HackathonDetail } from "@/lib/api/types";
import { Reveal } from "@/components/animation/Reveal";

// Cursor-paginated, so showing *all* of them means walking every `next`
// link ourselves rather than just rendering the first page — same pattern
// as sitemap.ts's fetchAllCourses, capped the same way so a pagination bug
// can't spin forever.
async function fetchAllCompletedHackathons(): Promise<Hackathon[]> {
  const hackathons: Hackathon[] = [];
  let path: string | null = "/hackathons/?scope=completed";

  for (let guard = 0; path && guard < 100; guard++) {
    const page: CursorPage<Hackathon> = await apiFetch<CursorPage<Hackathon>>(path, {
      cache: "no-store",
    });
    hackathons.push(...page.results);
    path = page.next ? page.next.replace(API_BASE_URL, "") : null;
  }

  return hackathons;
}

// The list endpoint doesn't carry winners/gallery_images (kept light for the
// active/upcoming browsing case, where they're always empty anyway) — the
// showcase section below needs the full detail per completed hackathon, so
// this fetches each one individually rather than widening the shared list
// serializer for a section only this page uses.
async function listPreviousHackathons(): Promise<HackathonDetail[]> {
  const summaries = await fetchAllCompletedHackathons();
  const details = await Promise.all(summaries.map((h) => getHackathon(h.id).catch(() => null)));
  return details.filter((h): h is HackathonDetail => h !== null);
}

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

  // Run in parallel, not a waterfall — the two fetches are independent, and
  // the previous-hackathons one specifically is isolated with its own
  // .catch() so a failure there (it's supplementary) can't blank out an
  // otherwise-successful active/upcoming/completed listing with a full-page
  // error.
  const [scopedResult, previousHackathons] = await Promise.all([
    listHackathons({ scope })
      .then((page) => ({ hackathons: page.results, loadError: null }))
      .catch(() => ({
        hackathons: [] as Hackathon[],
        loadError: "We couldn't reach the hackathons API right now. Make sure it's running.",
      })),
    listPreviousHackathons().catch(() => []),
  ]);
  hackathons = scopedResult.hackathons;
  loadError = scopedResult.loadError;

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

      {previousHackathons.length > 0 && (
        <Reveal className="mt-20">
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">
            Previous hackathons
          </h2>
          <p className="mt-2 text-sm text-foreground/60">
            A look back at what past cohorts built — winners, prizes, and event highlights.
          </p>
          <div className="mt-8 space-y-8">
            {previousHackathons.map((hackathon) => (
              <PreviousHackathonCard key={hackathon.id} hackathon={hackathon} />
            ))}
          </div>
        </Reveal>
      )}
    </div>
  );
}
