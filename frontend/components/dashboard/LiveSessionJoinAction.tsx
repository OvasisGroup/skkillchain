"use client";

import { Loader2, PlayCircle, Video } from "lucide-react";
import { useState } from "react";
import { ApiError } from "@/lib/api/client";
import { getLiveSessionRecording, joinLiveSession } from "@/lib/api/liveSessions";
import type { LiveSession } from "@/lib/api/types";
import { useAuth } from "@/lib/auth/AuthContext";

export function LiveSessionJoinAction({ session }: { session: LiveSession }) {
  const { accessToken } = useAuth();
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

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
          ? "Recording not available yet."
          : err instanceof ApiError
            ? err.message_
            : "Couldn't load the recording."
      );
    } finally {
      setBusy(false);
    }
  }

  if (session.status === "ended") {
    return session.is_recorded ? (
      <div>
        <button
          type="button"
          onClick={handleWatchRecording}
          disabled={busy}
          className="flex items-center gap-1.5 text-teal-400 hover:underline disabled:opacity-50"
        >
          {busy ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <PlayCircle className="h-3.5 w-3.5" />}
          Watch recording
        </button>
        {message && <p className="mt-1 text-xs text-rose-400">{message}</p>}
      </div>
    ) : (
      <span className="text-foreground/30">—</span>
    );
  }

  if (session.status === "canceled") {
    return <span className="text-foreground/30">Canceled</span>;
  }

  return (
    <div>
      <button
        type="button"
        onClick={handleJoin}
        disabled={busy}
        className="flex items-center gap-1.5 text-teal-400 hover:underline disabled:opacity-50"
      >
        {busy ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Video className="h-3.5 w-3.5" />}
        Join
      </button>
      {message && <p className="mt-1 text-xs text-rose-400">{message}</p>}
    </div>
  );
}
