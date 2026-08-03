import { apiFetch } from "./client";
import type { AdminUser, CursorPage } from "./types";

export function listUsers(token: string, email?: string): Promise<CursorPage<AdminUser>> {
  const query = email ? `?email=${encodeURIComponent(email)}` : "";
  return apiFetch<CursorPage<AdminUser>>(`/admin/users/${query}`, { token, cache: "no-store" });
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
