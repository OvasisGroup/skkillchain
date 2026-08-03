import { apiFetch } from "./client";
import type { CursorPage, SupportTicket, SupportTicketMessage } from "./types";

export function listAdminTickets(token: string): Promise<SupportTicket[]> {
  return apiFetch<SupportTicket[]>("/admin/support-tickets/", { token, cache: "no-store" });
}

export function updateAdminTicket(
  ticketId: string,
  patch: Partial<Pick<SupportTicket, "assignee" | "status" | "priority">>,
  token: string
): Promise<SupportTicket> {
  return apiFetch<SupportTicket>(`/admin/support-tickets/${ticketId}/`, {
    method: "PATCH",
    token,
    body: patch,
  });
}

export function listTicketMessages(
  ticketId: string,
  token: string
): Promise<CursorPage<SupportTicketMessage>> {
  return apiFetch<CursorPage<SupportTicketMessage>>(`/support-tickets/${ticketId}/messages/`, {
    token,
    cache: "no-store",
  });
}

export function postTicketMessage(
  ticketId: string,
  body: string,
  token: string
): Promise<SupportTicketMessage> {
  return apiFetch<SupportTicketMessage>(`/support-tickets/${ticketId}/messages/`, {
    method: "POST",
    token,
    body: { body },
  });
}
