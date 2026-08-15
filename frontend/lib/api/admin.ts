import { apiFetch } from "./client";
import type { AdminUser, CursorPage, RoleCode } from "./types";

export function listUsers(
  token: string,
  filters?: { email?: string; role?: RoleCode }
): Promise<CursorPage<AdminUser>> {
  const query = new URLSearchParams(
    Object.entries(filters ?? {}).filter(([, v]) => v !== undefined && v !== "")
  ).toString();
  return apiFetch<CursorPage<AdminUser>>(`/admin/users/${query ? `?${query}` : ""}`, {
    token,
    cache: "no-store",
  });
}

export function updateUserStatus(
  userId: string,
  isActive: boolean,
  token: string
): Promise<AdminUser> {
  return apiFetch<AdminUser>(`/admin/users/${userId}/status/`, {
    method: "PATCH",
    token,
    body: { is_active: isActive },
  });
}
