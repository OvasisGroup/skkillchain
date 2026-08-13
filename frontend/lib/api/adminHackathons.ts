import { apiFetch } from "./client";
import type {
  CursorPage,
  Hackathon,
  HackathonCreateInput,
  HackathonGalleryImage,
  HackathonOrganizerRegistration,
  HackathonWinner,
  HackathonWinnerInput,
  HackathonWriteResult,
} from "./types";

// Moderation counterpart to lib/api/organizerHackathons.ts — same shapes,
// but scoped by the hackathons.manage permission instead of organizer
// ownership, so an admin can manage any hackathon regardless of who
// created it (see backend/apps/hackathons/views.py's "Moderation override"
// section for why these are separate endpoints rather than folded into
// the organizer ones).

export function listAdminHackathons(token: string): Promise<CursorPage<Hackathon>> {
  return apiFetch<CursorPage<Hackathon>>("/admin/hackathons/", { token, cache: "no-store" });
}

export function getAdminHackathon(
  hackathonId: string,
  token: string
): Promise<HackathonWriteResult> {
  return apiFetch<HackathonWriteResult>(`/admin/hackathons/${hackathonId}/`, {
    token,
    cache: "no-store",
  });
}

export function updateAdminHackathon(
  hackathonId: string,
  input: Partial<HackathonCreateInput>,
  token: string
): Promise<HackathonWriteResult> {
  return apiFetch<HackathonWriteResult>(`/admin/hackathons/${hackathonId}/`, {
    method: "PATCH",
    token,
    body: input,
  });
}

export function cancelAdminHackathon(hackathonId: string, token: string): Promise<Hackathon> {
  return apiFetch<Hackathon>(`/admin/hackathons/${hackathonId}/cancel/`, {
    method: "POST",
    token,
  });
}

export function listAdminHackathonRegistrations(
  hackathonId: string,
  token: string
): Promise<CursorPage<HackathonOrganizerRegistration>> {
  return apiFetch<CursorPage<HackathonOrganizerRegistration>>(
    `/admin/hackathons/${hackathonId}/registrations/`,
    { token, cache: "no-store" }
  );
}

export function declareAdminHackathonWinner(
  hackathonId: string,
  input: HackathonWinnerInput,
  token: string
): Promise<HackathonWinner> {
  return apiFetch<HackathonWinner>(`/admin/hackathons/${hackathonId}/winners/`, {
    method: "POST",
    token,
    body: input,
  });
}

export function listAdminHackathonGalleryImages(
  hackathonId: string,
  token: string
): Promise<CursorPage<HackathonGalleryImage>> {
  return apiFetch<CursorPage<HackathonGalleryImage>>(
    `/admin/hackathons/${hackathonId}/gallery-images/`,
    { token, cache: "no-store" }
  );
}

// multipart/form-data, not JSON — apiFetch sets Content-Type itself only
// when the body isn't FormData (see lib/api/client.ts), so a real File
// upload just needs to be handed a FormData body directly.
export function uploadAdminHackathonGalleryImage(
  hackathonId: string,
  file: File,
  caption: string,
  token: string
): Promise<HackathonGalleryImage> {
  const body = new FormData();
  body.append("image", file);
  if (caption) body.append("caption", caption);
  return apiFetch<HackathonGalleryImage>(`/admin/hackathons/${hackathonId}/gallery-images/`, {
    method: "POST",
    token,
    body,
  });
}

export function addAdminHackathonGalleryVideo(
  hackathonId: string,
  videoUrl: string,
  caption: string,
  token: string
): Promise<HackathonGalleryImage> {
  return apiFetch<HackathonGalleryImage>(`/admin/hackathons/${hackathonId}/gallery-images/`, {
    method: "POST",
    token,
    body: { video_url: videoUrl, caption },
  });
}

export function deleteAdminHackathonGalleryImage(
  hackathonId: string,
  imageId: string,
  token: string
): Promise<void> {
  return apiFetch<void>(`/admin/hackathons/${hackathonId}/gallery-images/${imageId}/`, {
    method: "DELETE",
    token,
  });
}
