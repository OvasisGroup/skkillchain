import { apiFetch } from "./client";
import type { EmailTemplate, NotificationTemplate } from "./types";

export function listNotificationTemplates(token: string): Promise<NotificationTemplate[]> {
  return apiFetch<NotificationTemplate[]>("/admin/notification-templates/", {
    token,
    cache: "no-store",
  });
}

export function updateNotificationTemplate(
  code: string,
  locale: string,
  patch: Partial<Pick<NotificationTemplate, "subject_template" | "body_template" | "is_active">>,
  token: string
): Promise<NotificationTemplate> {
  return apiFetch<NotificationTemplate>(
    `/admin/notification-templates/${code}/?locale=${encodeURIComponent(locale)}`,
    { method: "PATCH", token, body: patch }
  );
}

export function listEmailTemplates(token: string): Promise<EmailTemplate[]> {
  return apiFetch<EmailTemplate[]>("/admin/email-templates/", { token, cache: "no-store" });
}

export function updateEmailTemplate(
  code: string,
  locale: string,
  patch: Partial<Pick<EmailTemplate, "subject" | "html_body" | "text_body" | "is_active">>,
  token: string
): Promise<EmailTemplate> {
  return apiFetch<EmailTemplate>(
    `/admin/email-templates/${code}/?locale=${encodeURIComponent(locale)}`,
    { method: "PATCH", token, body: patch }
  );
}
