"use client";

import { Bell, BellOff } from "lucide-react";
import { useEffect, useState } from "react";
import { ErrorState, LoadingState } from "@/components/dashboard/DashboardStates";
import { ApiError } from "@/lib/api/client";
import { listNotifications, markNotificationsRead } from "@/lib/api/notifications";
import type { Notification } from "@/lib/api/types";
import { useAuth } from "@/lib/auth/AuthContext";
import { Reveal } from "@/components/animation/Reveal";

export default function NotificationsPage() {
  const { accessToken } = useAuth();
  const [items, setItems] = useState<Notification[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [markingAll, setMarkingAll] = useState(false);

  useEffect(() => {
    if (!accessToken) return;
    let cancelled = false;
    listNotifications(accessToken)
      .then((page) => {
        if (!cancelled) setItems(page.results);
      })
      .catch((err) => {
        if (!cancelled)
          setError(err instanceof ApiError ? err.message_ : "Couldn't load your notifications.");
      });
    return () => {
      cancelled = true;
    };
  }, [accessToken]);

  async function handleMarkRead(id: string) {
    if (!accessToken) return;
    try {
      await markNotificationsRead(accessToken, [id]);
      setItems(
        (prev) =>
          prev?.map((n) => (n.id === id ? { ...n, read_at: new Date().toISOString() } : n)) ?? prev
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't mark this as read.");
    }
  }

  async function handleMarkAllRead() {
    if (!accessToken) return;
    setMarkingAll(true);
    try {
      await markNotificationsRead(accessToken);
      const now = new Date().toISOString();
      setItems((prev) => prev?.map((n) => (n.read_at ? n : { ...n, read_at: now })) ?? prev);
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't mark notifications as read.");
    } finally {
      setMarkingAll(false);
    }
  }

  const unreadCount = items?.filter((n) => !n.read_at).length ?? 0;

  return (
    <Reveal className="mx-auto max-w-4xl px-6 py-16">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wider text-lime-400">Inbox</p>
          <h1 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            Notifications
          </h1>
        </div>
        {!!items?.length && unreadCount > 0 && (
          <button
            type="button"
            onClick={handleMarkAllRead}
            disabled={markingAll}
            className="rounded-full border border-border-strong px-4 py-2 text-sm font-medium text-foreground/80 transition-colors hover:bg-surface-hover disabled:cursor-not-allowed disabled:opacity-50"
          >
            {markingAll ? "Marking…" : "Mark all as read"}
          </button>
        )}
      </div>

      {error && (
        <div className="mt-10">
          <ErrorState message={error} />
        </div>
      )}

      {!error && !items && <LoadingState label="Loading your notifications…" />}

      {!error && items && items.length === 0 && (
        <div className="mt-16 flex flex-col items-center rounded-2xl border border-dashed border-border-strong py-20 text-center">
          <BellOff className="h-10 w-10 text-foreground/30" />
          <p className="mt-4 text-sm text-foreground/50">You&apos;re all caught up — no notifications yet.</p>
        </div>
      )}

      {!error && items && items.length > 0 && (
        <div className="mt-10 divide-y divide-border rounded-2xl border border-border bg-surface">
          {items.map((n) => (
            <button
              key={n.id}
              type="button"
              onClick={() => !n.read_at && handleMarkRead(n.id)}
              className={`flex w-full items-start gap-3 p-5 text-left transition-colors hover:bg-surface-hover ${
                n.read_at ? "" : "bg-teal-400/5"
              }`}
            >
              <Bell className={`mt-0.5 h-5 w-5 flex-none ${n.read_at ? "text-foreground/30" : "text-teal-400"}`} />
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-semibold text-foreground">{n.title}</p>
                  {!n.read_at && <span className="h-2 w-2 flex-none rounded-full bg-rose-500" />}
                </div>
                <p className="mt-1 text-sm text-foreground/60">{n.body}</p>
                <p className="mt-2 text-xs text-foreground/40">
                  {new Date(n.created_at).toLocaleString()}
                </p>
              </div>
            </button>
          ))}
        </div>
      )}
    </Reveal>
  );
}
