import { apiFetch } from "./client";
import type {
  CursorPage,
  Hackathon,
  HackathonCreateInput,
  HackathonOrganizerRegistration,
  HackathonWinner,
  HackathonWinnerInput,
  HackathonWriteResult,
} from "./types";

export function listOrganizerHackathons(token: string): Promise<CursorPage<Hackathon>> {
  return apiFetch<CursorPage<Hackathon>>("/organizer/hackathons/", { token, cache: "no-store" });
}

export function getOrganizerHackathon(
  hackathonId: string,
  token: string
): Promise<HackathonWriteResult> {
  return apiFetch<HackathonWriteResult>(`/organizer/hackathons/${hackathonId}/`, {
    token,
    cache: "no-store",
  });
}

export function createHackathon(
  input: HackathonCreateInput,
  token: string
): Promise<HackathonWriteResult> {
  return apiFetch<HackathonWriteResult>("/organizer/hackathons/", {
    method: "POST",
    token,
    body: input,
  });
}

export function updateHackathon(
  hackathonId: string,
  input: Partial<HackathonCreateInput>,
  token: string
): Promise<HackathonWriteResult> {
  return apiFetch<HackathonWriteResult>(`/organizer/hackathons/${hackathonId}/`, {
    method: "PATCH",
    token,
    body: input,
  });
}

export function publishHackathon(hackathonId: string, token: string): Promise<Hackathon> {
  return apiFetch<Hackathon>(`/organizer/hackathons/${hackathonId}/publish/`, {
    method: "POST",
    token,
  });
}

export function cancelHackathon(hackathonId: string, token: string): Promise<Hackathon> {
  return apiFetch<Hackathon>(`/organizer/hackathons/${hackathonId}/cancel/`, {
    method: "POST",
    token,
  });
}

export function listHackathonRegistrations(
  hackathonId: string,
  token: string
): Promise<CursorPage<HackathonOrganizerRegistration>> {
  return apiFetch<CursorPage<HackathonOrganizerRegistration>>(
    `/organizer/hackathons/${hackathonId}/registrations/`,
    { token, cache: "no-store" }
  );
}

export function declareHackathonWinner(
  hackathonId: string,
  input: HackathonWinnerInput,
  token: string
): Promise<HackathonWinner> {
  return apiFetch<HackathonWinner>(`/organizer/hackathons/${hackathonId}/winners/`, {
    method: "POST",
    token,
    body: input,
  });
}
