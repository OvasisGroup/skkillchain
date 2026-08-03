"use client";

import { useEffect, useState } from "react";
import { LiveSessionCard } from "@/components/LiveSessionCard";
import { listMyLiveSessions } from "@/lib/api/liveSessions";
import type { Course, LiveSession } from "@/lib/api/types";
import { useAuth } from "@/lib/auth/AuthContext";

export interface CourseLiveSessionEntry {
  session: LiveSession;
  course: Course;
}

function SessionGroup({
  title,
  entries,
  registeredIds,
  onRegisteredChange,
  emptyMessage,
}: {
  title: string;
  entries: CourseLiveSessionEntry[];
  registeredIds: Set<string>;
  onRegisteredChange: (sessionId: string, registered: boolean) => void;
  emptyMessage: string;
}) {
  return (
    <section>
      <h2 className="text-lg font-semibold text-foreground">{title}</h2>
      {entries.length === 0 ? (
        <p className="mt-3 text-sm text-foreground/50">{emptyMessage}</p>
      ) : (
        <div className="mt-4 space-y-3">
          {entries.map(({ session, course }) => (
            <LiveSessionCard
              key={session.id}
              session={session}
              isRegistered={registeredIds.has(session.id)}
              onRegisteredChange={onRegisteredChange}
              loginRedirectPath="/live-sessions"
              courseLabel={course.title}
              courseHref={`/courses/${course.id}`}
            />
          ))}
        </div>
      )}
    </section>
  );
}

export function LiveSessionsBrowser({ entries }: { entries: CourseLiveSessionEntry[] }) {
  const { accessToken, isAuthenticated } = useAuth();
  const [registeredIds, setRegisteredIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (!accessToken) return;
    let cancelled = false;
    listMyLiveSessions(accessToken)
      .then((mine) => {
        if (!cancelled) setRegisteredIds(new Set(mine.map((s) => s.id)));
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [accessToken, isAuthenticated]);

  function handleRegisteredChange(sessionId: string, registered: boolean) {
    setRegisteredIds((prev) => {
      const next = new Set(prev);
      if (registered) next.add(sessionId);
      else next.delete(sessionId);
      return next;
    });
  }

  const live = entries
    .filter((e) => e.session.status === "live")
    .sort((a, b) => a.session.scheduled_start_at.localeCompare(b.session.scheduled_start_at));
  const upcoming = entries
    .filter((e) => e.session.status === "scheduled")
    .sort((a, b) => a.session.scheduled_start_at.localeCompare(b.session.scheduled_start_at));
  const past = entries
    .filter((e) => e.session.status === "ended")
    .sort((a, b) => b.session.scheduled_start_at.localeCompare(a.session.scheduled_start_at));

  if (entries.length === 0) {
    return (
      <div className="mt-16 flex flex-col items-center rounded-2xl border border-dashed border-border-strong py-20 text-center">
        <p className="text-sm text-foreground/50">No live sessions scheduled yet — check back soon.</p>
      </div>
    );
  }

  return (
    <div className="mt-12 space-y-12">
      {live.length > 0 && (
        <SessionGroup
          title="Live now"
          entries={live}
          registeredIds={registeredIds}
          onRegisteredChange={handleRegisteredChange}
          emptyMessage=""
        />
      )}
      <SessionGroup
        title="Upcoming"
        entries={upcoming}
        registeredIds={registeredIds}
        onRegisteredChange={handleRegisteredChange}
        emptyMessage="Nothing scheduled right now — check back soon."
      />
      {past.length > 0 && (
        <SessionGroup
          title="Past sessions"
          entries={past}
          registeredIds={registeredIds}
          onRegisteredChange={handleRegisteredChange}
          emptyMessage=""
        />
      )}
    </div>
  );
}
