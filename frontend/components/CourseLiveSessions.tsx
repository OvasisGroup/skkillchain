"use client";

import { Radio } from "lucide-react";
import { useEffect, useState } from "react";
import { LiveSessionCard } from "@/components/LiveSessionCard";
import { listMyLiveSessions } from "@/lib/api/liveSessions";
import type { LiveSession } from "@/lib/api/types";
import { useAuth } from "@/lib/auth/AuthContext";

export function CourseLiveSessions({
  courseId,
  sessions,
}: {
  courseId: string;
  sessions: LiveSession[];
}) {
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

  if (sessions.length === 0) return null;

  return (
    <div className="mt-10">
      <h2 className="flex items-center gap-2 text-lg font-semibold text-foreground">
        <Radio className="h-5 w-5 text-teal-400" />
        Live sessions
      </h2>
      <div className="mt-4 space-y-3">
        {sessions.map((session) => (
          <LiveSessionCard
            key={session.id}
            session={session}
            isRegistered={registeredIds.has(session.id)}
            onRegisteredChange={handleRegisteredChange}
            loginRedirectPath={`/courses/${courseId}`}
          />
        ))}
      </div>
    </div>
  );
}
