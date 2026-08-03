import { apiFetch } from "./client";
import type { InstructorDetail, InstructorSummary } from "./types";

export function listInstructors(): Promise<InstructorSummary[]> {
  return apiFetch<InstructorSummary[]>("/instructors/", { cache: "no-store" });
}

export function getInstructor(id: string): Promise<InstructorDetail> {
  return apiFetch<InstructorDetail>(`/instructors/${id}/`, { cache: "no-store" });
}
