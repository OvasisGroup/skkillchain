"use client";

import { CalendarClock, Loader2, PlayCircle, Video } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { ApiError } from "@/lib/api/client";
import {
  cancelLiveSessionRegistration,
  getLiveSessionRecording,
  joinLiveSession,
  registerForLiveSession,
} from "@/lib/api/liveSessions";
import type { LiveSession } from "@/lib/api/types";
import { useAuth } from "@/lib/auth/AuthContext";

const STATUS_STYLES: Record<LiveSession["status"], string> = {
  scheduled: "bg-teal-400/10 text-teal-400",
  live: "bg-emerald-500/10 text-emerald-400",
  ended: "bg-foreground/10 text-foreground/50",
  canceled: "bg-rose-500/10 text-rose-400",
};

export function LiveSessionCard({
  session,
  isRegistered,
  onRegisteredChange,
  loginRedirectPath,
  courseLabel,
  courseHref,
}: {
  session: LiveSession;
  isRegistered: boolean;
  onRegisteredChange: (sessionId: string, registered: boolean) => void;
  loginRedirectPath: string;
  courseLabel?: string;
  courseHref?: string;
}) {
  const { accessToken, isAuthenticated } = useAuth();
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function handleRegister() {
    if (!accessToken) return;
    setBusy(true);
    setMessage(null);
    try {
      await registerForLiveSession(session.id, accessToken);
      onRegisteredChange(session.id, true);
    } catch (err) {
      setMessage(err instanceof ApiError ? err.message_ : "Couldn't register for this session.");
    } finally {
      setBusy(false);
    }
  }

  async function handleCancelRegistration() {
    if (!accessToken) return;
    setBusy(true);
    setMessage(null);
    try {
      await cancelLiveSessionRegistration(session.id, accessToken);
      onRegisteredChange(session.id, false);
    } catch (err) {
      setMessage(err instanceof ApiError ? err.message_ : "Couldn't cancel your registration.");
    } finally {
      setBusy(false);
    }
  }

  async function handleJoin() {
    if (!accessToken) return;
    setBusy(true);
    setMessage(null);
    try {
      const { join_url } = await joinLiveSession(session.id, accessToken);
      window.open(join_url, "_blank", "noopener,noreferrer");
    } catch (err) {
      setMessage(err instanceof ApiError ? err.message_ : "Couldn't join this session.");
    } finally {
      setBusy(false);
    }
  }

  async function handleWatchRecording() {
    if (!accessToken) return;
    setBusy(true);
    setMessage(null);
    try {
      const recording = await getLiveSessionRecording(session.id, accessToken);
      window.open(recording.playback_url, "_blank", "noopener,noreferrer");
    } catch (err) {
      setMessage(
        err instanceof ApiError && err.status === 404
          ? "Recording not available for this session."
          : err instanceof ApiError
            ? err.message_
            : "Couldn't load the recording."
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-col gap-3 rounded-xl border border-border bg-surface p-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <p className="font-medium text-foreground">{session.title}</p>
          <span
            className={`rounded-full px-2 py-0.5 text-xs font-medium capitalize ${STATUS_STYLES[session.status]}`}
          >
            {session.status}
          </span>
          {courseLabel && courseHref && (
            <Link
              href={courseHref}
              className="rounded-full bg-surface-hover px-2 py-0.5 text-xs font-medium text-foreground/60 hover:text-teal-400"
            >
              {courseLabel}
            </Link>
          )}
        </div>
        {session.description && (
          <p className="mt-1 text-sm text-foreground/60">{session.description}</p>
        )}
        <p className="mt-1 flex items-center gap-1.5 text-xs text-foreground/50">
          <CalendarClock className="h-3.5 w-3.5" />
          {new Date(session.scheduled_start_at).toLocaleString()}
        </p>
        {message && <p className="mt-1 text-xs text-rose-400">{message}</p>}
      </div>

      <div className="flex flex-none items-center gap-2">
        {!isAuthenticated && (
          <Link
            href={`/login?next=${encodeURIComponent(loginRedirectPath)}`}
            className="rounded-full border border-border-strong px-4 py-1.5 text-xs font-semibold text-foreground/80 transition-colors hover:bg-surface-hover"
          >
            Log in to register
          </Link>
        )}

        {isAuthenticated && session.status !== "ended" && session.status !== "canceled" && (
          <>
            {isRegistered ? (
              <>
                <button
                  type="button"
                  onClick={handleJoin}
                  disabled={busy}
                  className="flex items-center gap-1.5 rounded-full bg-teal-400 px-4 py-1.5 text-xs font-semibold text-emerald-950 transition-opacity hover:opacity-90 disabled:opacity-50"
                >
                  {busy ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Video className="h-3.5 w-3.5" />}
                  Join
                </button>
                <button
                  type="button"
                  onClick={handleCancelRegistration}
                  disabled={busy}
                  className="rounded-full border border-border-strong px-3 py-1.5 text-xs font-semibold text-foreground/70 transition-colors hover:bg-surface-hover disabled:opacity-50"
                >
                  Cancel
                </button>
              </>
            ) : (
              <button
                type="button"
                onClick={handleRegister}
                disabled={busy}
                className="flex items-center gap-1.5 rounded-full bg-teal-400 px-4 py-1.5 text-xs font-semibold text-emerald-950 transition-opacity hover:opacity-90 disabled:opacity-50"
              >
                {busy && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                Register
              </button>
            )}
          </>
        )}

        {isAuthenticated && session.status === "ended" && session.is_recorded && (
          <button
            type="button"
            onClick={handleWatchRecording}
            disabled={busy}
            className="flex items-center gap-1.5 rounded-full border border-border-strong px-4 py-1.5 text-xs font-semibold text-foreground/80 transition-colors hover:bg-surface-hover disabled:opacity-50"
          >
            <PlayCircle className="h-3.5 w-3.5" /> Watch recording
          </button>
        )}
      </div>
    </div>
  );
}
