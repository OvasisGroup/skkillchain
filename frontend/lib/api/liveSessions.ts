import { apiFetch } from "./client";
import type {
  ConferencingAccount,
  ConferencingProvider,
  LiveSession,
  LiveSessionCreateInput,
  LiveSessionRecording,
  LiveSessionRegistration,
  LiveSessionUpdateInput,
} from "./types";

// ---------- Instructor: conferencing accounts ----------

export function connectConferencingAccount(
  provider: ConferencingProvider,
  token: string
): Promise<{ authorization_url: string }> {
  return apiFetch<{ authorization_url: string }>(
    `/instructor/conferencing-accounts/${provider}/connect/`,
    { method: "POST", token }
  );
}

export function listConferencingAccounts(token: string): Promise<ConferencingAccount[]> {
  return apiFetch<ConferencingAccount[]>("/instructor/conferencing-accounts/", {
    token,
    cache: "no-store",
  });
}

export function revokeConferencingAccount(accountId: string, token: string): Promise<void> {
  return apiFetch<void>(`/instructor/conferencing-accounts/${accountId}/`, {
    method: "DELETE",
    token,
  });
}

// ---------- Instructor: scheduling ----------

export function scheduleLiveSession(
  courseId: string,
  input: LiveSessionCreateInput,
  token: string
): Promise<LiveSession> {
  return apiFetch<LiveSession>(`/instructor/courses/${courseId}/live-sessions/`, {
    method: "POST",
    token,
    body: input,
  });
}

export function updateLiveSession(
  id: string,
  input: LiveSessionUpdateInput,
  token: string
): Promise<LiveSession> {
  return apiFetch<LiveSession>(`/instructor/live-sessions/${id}/`, {
    method: "PATCH",
    token,
    body: input,
  });
}

export function cancelLiveSession(id: string, token: string): Promise<LiveSession> {
  return apiFetch<LiveSession>(`/instructor/live-sessions/${id}/cancel/`, {
    method: "POST",
    token,
  });
}

export function listLiveSessionRegistrations(
  id: string,
  token: string
): Promise<LiveSessionRegistration[]> {
  return apiFetch<LiveSessionRegistration[]>(`/instructor/live-sessions/${id}/registrations/`, {
    token,
    cache: "no-store",
  });
}

// ---------- Student: discovery, registration, join ----------

export function listCourseLiveSessions(courseId: string): Promise<LiveSession[]> {
  return apiFetch<LiveSession[]>(`/courses/${courseId}/live-sessions/`, { cache: "no-store" });
}

export function listMyLiveSessions(token: string): Promise<LiveSession[]> {
  return apiFetch<LiveSession[]>("/students/me/live-sessions/", { token, cache: "no-store" });
}

export function registerForLiveSession(id: string, token: string): Promise<void> {
  return apiFetch<void>(`/live-sessions/${id}/register/`, { method: "POST", token });
}

export function cancelLiveSessionRegistration(id: string, token: string): Promise<void> {
  return apiFetch<void>(`/live-sessions/${id}/register/`, { method: "DELETE", token });
}

export function joinLiveSession(id: string, token: string): Promise<{ join_url: string }> {
  return apiFetch<{ join_url: string }>(`/live-sessions/${id}/join/`, { token });
}

export function getLiveSessionRecording(
  id: string,
  token: string
): Promise<LiveSessionRecording> {
  return apiFetch<LiveSessionRecording>(`/live-sessions/${id}/recording/`, {
    token,
    cache: "no-store",
  });
}
