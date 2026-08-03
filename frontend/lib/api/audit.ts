import { apiFetch } from "./client";
import type { AuditLog, CursorPage } from "./types";

export function listAuditLogs(token: string, action?: string): Promise<CursorPage<AuditLog>> {
  const query = action ? `?action=${encodeURIComponent(action)}` : "";
  return apiFetch<CursorPage<AuditLog>>(`/admin/audit-logs/${query}`, {
    token,
    cache: "no-store",
  });
}
