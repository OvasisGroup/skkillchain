import { apiFetch } from "./client";
import type { CursorPage, Notification } from "./types";

export function listNotifications(token: string): Promise<CursorPage<Notification>> {
  return apiFetch<CursorPage<Notification>>("/notifications/", { token, cache: "no-store" });
}

export function markNotificationsRead(
  token: string,
  notificationIds?: string[]
): Promise<{ marked_read: number }> {
  return apiFetch<{ marked_read: number }>("/notifications/mark-read/", {
    method: "POST",
    token,
    body: notificationIds ? { notification_ids: notificationIds } : {},
  });
}
