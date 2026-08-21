import { apiFetch } from "./client";
import type { AdminUser, CursorPage, Profile, RoleCode } from "./types";

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

// Admin counterpart to lib/api/auth.ts's updateMe()/uploadAvatar() — same
// split (avatar travels through its own multipart endpoint, never the JSON
// PATCH body) but scoped by userId + the users.manage permission instead
// of the caller's own session.
export function getAdminUserProfile(userId: string, token: string): Promise<Profile> {
  return apiFetch<Profile>(`/admin/users/${userId}/profile/`, { token, cache: "no-store" });
}

export function updateAdminUserProfile(
  userId: string,
  input: Partial<Omit<Profile, "avatar">>,
  token: string
): Promise<Profile> {
  return apiFetch<Profile>(`/admin/users/${userId}/profile/`, {
    method: "PATCH",
    token,
    body: input,
  });
}

export function uploadAdminUserAvatar(userId: string, file: File, token: string): Promise<Profile> {
  const form = new FormData();
  form.set("avatar", file);
  return apiFetch<Profile>(`/admin/users/${userId}/avatar/`, {
    method: "POST",
    token,
    body: form,
  });
}
