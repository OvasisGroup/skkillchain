import { Building2, Calendar, ExternalLink, FileText, Trophy, Users } from "lucide-react";
import Link from "next/link";
import { notFound } from "next/navigation";
import { HackathonRegisterButton } from "@/components/HackathonRegisterButton";
import { ApiError } from "@/lib/api/client";
import { getHackathon } from "@/lib/api/hackathons";
import type { HackathonDetail } from "@/lib/api/types";
import { SITE_NAME, absoluteUrl, safeJsonLd } from "@/lib/seo";
import { Reveal } from "@/components/animation/Reveal";

const PHASE_STYLES: Record<HackathonDetail["phase"], string> = {
  draft: "bg-foreground/10 text-foreground/60",
  upcoming: "bg-amber-500/10 text-amber-400",
  active: "bg-emerald-500/10 text-emerald-400",
  completed: "bg-foreground/10 text-foreground/50",
  canceled: "bg-rose-500/10 text-rose-400",
};

function formatDateTime(value: string): string {
  return new Date(value).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  try {
    const hackathon = await getHackathon(id);
    const canonical = `/hackathons/${hackathon.id}`;
    return {
      title: hackathon.title,
      description: hackathon.summary,
      alternates: { canonical },
      openGraph: {
        type: "website",
        url: absoluteUrl(canonical),
        title: hackathon.title,
        description: hackathon.summary,
        ...(hackathon.cover_image ? { images: [{ url: hackathon.cover_image }] } : {}),
      },
    };
  } catch {
    return { title: "Hackathon" };
  }
}

function hackathonJsonLd(hackathon: HackathonDetail) {
  return {
    "@context": "https://schema.org",
    "@type": "Event",
    name: hackathon.title,
    description: hackathon.summary,
    url: absoluteUrl(`/hackathons/${hackathon.id}`),
    startDate: hackathon.starts_at,
    endDate: hackathon.ends_at,
    eventStatus:
      hackathon.phase === "canceled"
        ? "https://schema.org/EventCancelled"
        : "https://schema.org/EventScheduled",
    organizer: {
      "@type": "Organization",
      name: hackathon.host_type === "partner" ? hackathon.partner_name || SITE_NAME : SITE_NAME,
    },
  };
}

export default async function HackathonDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  let hackathon: HackathonDetail;
  try {
    hackathon = await getHackathon(id);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) {
      notFound();
    }
    throw err;
  }

  return (
    <div className="mx-auto max-w-7xl px-6 py-16">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: safeJsonLd(hackathonJsonLd(hackathon)) }}
      />
      <nav className="text-sm text-foreground/40">
        <Link href="/hackathons" className="hover:text-foreground">
          Hackathons
        </Link>
        <span className="mx-2">/</span>
        <span className="text-foreground">{hackathon.title}</span>
      </nav>

      <div className="mt-8 grid grid-cols-1 gap-12 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <Reveal>
            <div className="flex flex-wrap items-center gap-2">
              <span
                className={`rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${PHASE_STYLES[hackathon.phase]}`}
              >
                {hackathon.phase}
              </span>
              {hackathon.host_type === "partner" && (
                <span className="flex items-center gap-1 rounded-full bg-surface-hover px-2.5 py-0.5 text-xs font-medium text-foreground/70">
                  <Building2 className="h-3.5 w-3.5" />
                  In partnership with {hackathon.partner_name}
                </span>
              )}
            </div>

            <h1 className="mt-4 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
              {hackathon.title}
            </h1>
            <p className="mt-4 text-lg leading-8 text-foreground/60">{hackathon.summary}</p>

            <div className="mt-6 flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-foreground/50">
              <span className="flex items-center gap-1.5">
                <Calendar className="h-4 w-4" />
                {formatDateTime(hackathon.starts_at)} – {formatDateTime(hackathon.ends_at)}
              </span>
              {hackathon.capacity !== null && (
                <span className="flex items-center gap-1.5">
                  <Users className="h-4 w-4" />
                  {hackathon.registered_count} / {hackathon.capacity} registered
                </span>
              )}
              {hackathon.partner_url && (
                <a
                  href={hackathon.partner_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1.5 hover:text-foreground"
                >
                  <ExternalLink className="h-4 w-4" />
                  Partner site
                </a>
              )}
            </div>
          </Reveal>

          {hackathon.description && (
            <Reveal className="mt-10">
              <h2 className="text-lg font-semibold text-foreground">About this hackathon</h2>
              <p className="mt-3 whitespace-pre-line text-sm leading-7 text-foreground/60">
                {hackathon.description}
              </p>
            </Reveal>
          )}

          {hackathon.requirements && (
            <Reveal className="mt-10">
              <h2 className="text-lg font-semibold text-foreground">Requirements</h2>
              <p className="mt-3 whitespace-pre-line text-sm leading-7 text-foreground/60">
                {hackathon.requirements}
              </p>
            </Reveal>
          )}

          <Reveal className="mt-10">
            <h2 className="text-lg font-semibold text-foreground">Key dates</h2>
            <dl className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div className="rounded-xl border border-border bg-surface p-4">
                <dt className="text-xs uppercase tracking-wide text-foreground/40">
                  Registration deadline
                </dt>
                <dd className="mt-1 text-sm font-medium text-foreground">
                  {formatDateTime(hackathon.registration_deadline)}
                </dd>
              </div>
              <div className="rounded-xl border border-border bg-surface p-4">
                <dt className="text-xs uppercase tracking-wide text-foreground/40">
                  Submission deadline
                </dt>
                <dd className="mt-1 text-sm font-medium text-foreground">
                  {formatDateTime(hackathon.submission_deadline)}
                </dd>
              </div>
              <div className="rounded-xl border border-border bg-surface p-4">
                <dt className="text-xs uppercase tracking-wide text-foreground/40">Event window</dt>
                <dd className="mt-1 text-sm font-medium text-foreground">
                  {formatDateTime(hackathon.starts_at)} – {formatDateTime(hackathon.ends_at)}
                </dd>
              </div>
            </dl>
          </Reveal>

          {hackathon.winners.length > 0 && (
            <Reveal className="mt-10">
              <h2 className="text-lg font-semibold text-foreground">Winners</h2>
              <div className="mt-4 space-y-3">
                {hackathon.winners.map((winner) => (
                  <div
                    key={winner.id}
                    className="flex items-start gap-3 rounded-xl border border-border bg-surface p-4"
                  >
                    <Trophy className="mt-0.5 h-5 w-5 flex-none text-amber-400" />
                    <div>
                      <p className="text-sm font-semibold text-foreground">
                        #{winner.placement} — {winner.submission.title}
                      </p>
                      <p className="mt-1 text-xs text-foreground/50">{winner.participant.email}</p>
                      {winner.prize_description && (
                        <p className="mt-1 text-sm text-foreground/60">{winner.prize_description}</p>
                      )}
                      {winner.submission.repo_url && (
                        <a
                          href={winner.submission.repo_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="mt-1 inline-flex items-center gap-1 text-xs text-teal-400 hover:underline"
                        >
                          <FileText className="h-3.5 w-3.5" />
                          View project
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </Reveal>
          )}
        </div>

        <div className="lg:col-span-1">
          <div className="sticky top-24 overflow-hidden rounded-2xl border border-border bg-surface shadow-sm">
            {hackathon.cover_image ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={hackathon.cover_image}
                alt={hackathon.title}
                className="aspect-video w-full object-cover"
              />
            ) : (
              <div className="flex aspect-video items-center justify-center bg-emerald-500">
                <Trophy className="h-10 w-10 text-teal-950/80" strokeWidth={1.5} />
              </div>
            )}

            <div className="p-6">
              {hackathon.prize_summary && (
                <p className="text-2xl font-semibold text-foreground">{hackathon.prize_summary}</p>
              )}
              <div className="mt-6">
                <HackathonRegisterButton hackathon={hackathon} />
              </div>
              <ul className="mt-6 space-y-3 border-t border-border pt-6 text-sm text-foreground/60">
                <li className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-teal-400" />
                  Register by {formatDateTime(hackathon.registration_deadline)}
                </li>
                <li className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-teal-400" />
                  Submit by {formatDateTime(hackathon.submission_deadline)}
                </li>
                {hackathon.capacity !== null && (
                  <li className="flex items-center gap-2">
                    <Users className="h-4 w-4 text-teal-400" />
                    Capped at {hackathon.capacity} participants
                  </li>
                )}
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
