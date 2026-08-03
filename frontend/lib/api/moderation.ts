import { apiFetch } from "./client";
import type { CursorPage, InstructorApplication } from "./types";

export function applyAsInstructor(token: string): Promise<InstructorApplication> {
  return apiFetch<InstructorApplication>("/instructor/apply/", { method: "POST", token });
}

export function listInstructorApplications(
  token: string,
  status?: "pending" | "approved"
): Promise<CursorPage<InstructorApplication>> {
  const query = status ? `?status=${status}` : "";
  return apiFetch<CursorPage<InstructorApplication>>(`/admin/instructors/${query}`, {
    token,
    cache: "no-store",
  });
}

export function approveInstructorApplication(
  userId: string,
  token: string
): Promise<InstructorApplication> {
  return apiFetch<InstructorApplication>(`/admin/instructors/${userId}/approve/`, {
    method: "POST",
    token,
  });
}
