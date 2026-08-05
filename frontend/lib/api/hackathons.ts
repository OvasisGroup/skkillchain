import { apiFetch } from "./client";
import type {
  CursorPage,
  Hackathon,
  HackathonDetail,
  HackathonRegistration,
  HackathonRegistrationInput,
  HackathonSubmission,
  HackathonSubmissionInput,
} from "./types";

export type HackathonScope = "active" | "upcoming" | "completed" | "all";

export function listHackathons(params: {
  scope?: HackathonScope;
  host_type?: "internal" | "partner";
} = {}): Promise<CursorPage<Hackathon>> {
  const query = new URLSearchParams();
  if (params.scope) query.set("scope", params.scope);
  if (params.host_type) query.set("host_type", params.host_type);
  const qs = query.toString();
  return apiFetch<CursorPage<Hackathon>>(`/hackathons/${qs ? `?${qs}` : ""}`, {
    cache: "no-store",
  });
}

export function getHackathon(hackathonId: string): Promise<HackathonDetail> {
  return apiFetch<HackathonDetail>(`/hackathons/${hackathonId}/`, { cache: "no-store" });
}

export function registerForHackathon(
  hackathonId: string,
  input: HackathonRegistrationInput,
  token: string
): Promise<void> {
  return apiFetch<void>(`/hackathons/${hackathonId}/register/`, {
    method: "POST",
    token,
    body: input,
  });
}

export function withdrawFromHackathon(hackathonId: string, token: string): Promise<void> {
  return apiFetch<void>(`/hackathons/${hackathonId}/register/`, { method: "DELETE", token });
}

export function submitHackathonProject(
  hackathonId: string,
  input: HackathonSubmissionInput,
  token: string
): Promise<HackathonSubmission> {
  return apiFetch<HackathonSubmission>(`/hackathons/${hackathonId}/submission/`, {
    method: "POST",
    token,
    body: input,
  });
}

export function listMyHackathonRegistrations(token: string): Promise<CursorPage<HackathonRegistration>> {
  return apiFetch<CursorPage<HackathonRegistration>>("/students/me/hackathons/", {
    token,
    cache: "no-store",
  });
}
