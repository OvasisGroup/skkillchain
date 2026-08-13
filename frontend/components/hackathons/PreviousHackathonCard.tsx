import { Medal, Trophy, UserRound } from "lucide-react";
import type { HackathonDetail, HackathonWinner } from "@/lib/api/types";
import { HackathonGalleryViewer } from "./HackathonGalleryViewer";

function winnerDisplayName(winner: HackathonWinner): string {
  const name = `${winner.participant.profile.first_name} ${winner.participant.profile.last_name}`.trim();
  return name || winner.participant.email;
}

// Gold / silver / bronze — placements beyond 3rd (rare, but the backend
// allows any positive placement) fall back to a neutral badge rather than
// repeating bronze or guessing a color that doesn't mean anything past 3rd.
const PLACEMENT_STYLES: Record<number, { label: string; badge: string; icon: typeof Trophy }> = {
  1: { label: "1st place", badge: "bg-amber-400/15 text-amber-400", icon: Trophy },
  2: { label: "2nd place", badge: "bg-slate-400/15 text-slate-300", icon: Medal },
  3: { label: "3rd place", badge: "bg-orange-600/15 text-orange-400", icon: Medal },
};

function formatDateRange(startsAt: string, endsAt: string): string {
  const start = new Date(startsAt);
  const end = new Date(endsAt);
  const fmt: Intl.DateTimeFormatOptions = { month: "short", day: "numeric", year: "numeric" };
  return `${start.toLocaleDateString(undefined, fmt)} – ${end.toLocaleDateString(undefined, fmt)}`;
}

export function PreviousHackathonCard({ hackathon }: { hackathon: HackathonDetail }) {
  const winners = [...hackathon.winners].sort((a, b) => a.placement - b.placement);

  return (
    <div className="overflow-hidden rounded-2xl border border-border bg-surface shadow-sm">
      <div className="relative flex aspect-[21/9] items-center justify-center overflow-hidden bg-emerald-500">
        {hackathon.cover_image ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={hackathon.cover_image}
            alt=""
            className="absolute inset-0 h-full w-full object-cover"
          />
        ) : (
          <Trophy className="h-10 w-10 text-teal-950/80" strokeWidth={1.5} />
        )}
      </div>

      <div className="p-6 sm:p-8">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-foreground/50">
          <span>{formatDateRange(hackathon.starts_at, hackathon.ends_at)}</span>
          {hackathon.host_type === "partner" && hackathon.partner_name && (
            <>
              <span aria-hidden="true">·</span>
              <span>In partnership with {hackathon.partner_name}</span>
            </>
          )}
        </div>
        <h3 className="mt-2 text-xl font-semibold text-foreground">{hackathon.title}</h3>
        {(hackathon.description || hackathon.summary) && (
          <p className="mt-3 whitespace-pre-line text-sm leading-7 text-foreground/60">
            {hackathon.description || hackathon.summary}
          </p>
        )}

        {winners.length > 0 && (
          <div className="mt-8">
            <h4 className="text-sm font-semibold text-foreground">Winners &amp; prizes</h4>
            <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-3">
              {winners.map((winner) => {
                const style = PLACEMENT_STYLES[winner.placement] ?? {
                  label: `#${winner.placement}`,
                  badge: "bg-foreground/10 text-foreground/60",
                  icon: Medal,
                };
                const Icon = style.icon;
                return (
                  <div
                    key={winner.id}
                    className="flex flex-col items-center rounded-xl border border-border bg-background/40 p-4 text-center"
                  >
                    <div className="h-16 w-16 flex-none overflow-hidden rounded-full border-2 border-border-strong bg-surface-hover">
                      {winner.participant.profile.avatar ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img
                          src={winner.participant.profile.avatar}
                          alt=""
                          className="h-full w-full object-cover"
                        />
                      ) : (
                        <div className="flex h-full w-full items-center justify-center">
                          <UserRound className="h-8 w-8 text-foreground/30" strokeWidth={1.5} />
                        </div>
                      )}
                    </div>
                    <span
                      className={`mt-3 inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${style.badge}`}
                    >
                      <Icon className="h-3.5 w-3.5" />
                      {style.label}
                    </span>
                    <p className="mt-2 text-sm font-semibold text-foreground">
                      {winnerDisplayName(winner)}
                    </p>
                    <p className="mt-0.5 text-xs text-foreground/50">{winner.submission.title}</p>
                    {winner.prize_description && (
                      <p className="mt-2 text-sm font-medium text-teal-400">
                        {winner.prize_description}
                      </p>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {hackathon.gallery_images.length > 0 && (
          <div className="mt-8">
            <HackathonGalleryViewer images={hackathon.gallery_images} />
          </div>
        )}
      </div>
    </div>
  );
}
