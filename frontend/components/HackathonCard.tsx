import { Building2, Trophy } from "lucide-react";
import Link from "next/link";
import type { Hackathon } from "@/lib/api/types";

const PHASE_STYLES: Record<Hackathon["phase"], string> = {
  draft: "bg-foreground/10 text-foreground/60",
  upcoming: "bg-amber-500/10 text-amber-400",
  active: "bg-emerald-500/10 text-emerald-400",
  completed: "bg-foreground/10 text-foreground/50",
  canceled: "bg-rose-500/10 text-rose-400",
};

function formatDateRange(startsAt: string, endsAt: string): string {
  const start = new Date(startsAt);
  const end = new Date(endsAt);
  const fmt: Intl.DateTimeFormatOptions = { month: "short", day: "numeric" };
  return `${start.toLocaleDateString(undefined, fmt)} – ${end.toLocaleDateString(undefined, fmt)}`;
}

export function HackathonCard({ hackathon }: { hackathon: Hackathon }) {
  return (
    <Link
      href={`/hackathons/${hackathon.id}`}
      className="group flex flex-col overflow-hidden rounded-2xl border border-border bg-surface shadow-sm transition-all hover:-translate-y-0.5 hover:border-teal-400/50 hover:bg-surface-hover hover:shadow-md"
    >
      <div className="relative flex aspect-video items-center justify-center overflow-hidden bg-emerald-500">
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
        <span
          className={`absolute right-2.5 top-2.5 rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${PHASE_STYLES[hackathon.phase]}`}
        >
          {hackathon.phase}
        </span>
      </div>
      <div className="flex flex-1 flex-col p-5">
        <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-foreground/40">
          {hackathon.host_type === "partner" ? (
            <span className="flex items-center gap-1">
              <Building2 className="h-3.5 w-3.5" />
              {hackathon.partner_name || "Partner"}
            </span>
          ) : (
            <span>SkillChain</span>
          )}
        </div>
        <h3 className="mt-3 text-base font-semibold text-foreground group-hover:text-teal-600 dark:group-hover:text-teal-300">
          {hackathon.title}
        </h3>
        <p className="mt-1.5 line-clamp-2 flex-1 text-sm text-foreground/60">
          {hackathon.summary}
        </p>
        <div className="mt-4 flex items-center justify-between border-t border-border pt-4">
          <span className="text-xs text-foreground/50">
            {formatDateRange(hackathon.starts_at, hackathon.ends_at)}
          </span>
          {hackathon.prize_summary && (
            <span className="text-sm font-semibold text-foreground">{hackathon.prize_summary}</span>
          )}
        </div>
      </div>
    </Link>
  );
}
