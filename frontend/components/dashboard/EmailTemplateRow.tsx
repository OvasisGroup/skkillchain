"use client";

import { useState } from "react";
import { ApiError } from "@/lib/api/client";
import { updateEmailTemplate } from "@/lib/api/templates";
import type { EmailTemplate } from "@/lib/api/types";
import { useAuth } from "@/lib/auth/AuthContext";

export function EmailTemplateRow({
  template,
  onUpdated,
}: {
  template: EmailTemplate;
  onUpdated: (updated: EmailTemplate) => void;
}) {
  const { accessToken } = useAuth();
  const [editing, setEditing] = useState(false);
  const [subject, setSubject] = useState(template.subject);
  const [htmlBody, setHtmlBody] = useState(template.html_body);
  const [textBody, setTextBody] = useState(template.text_body);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSave() {
    if (!accessToken) return;
    setSaving(true);
    setError(null);
    try {
      const updated = await updateEmailTemplate(
        template.code,
        template.locale,
        { subject, html_body: htmlBody, text_body: textBody },
        accessToken
      );
      onUpdated(updated);
      setEditing(false);
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't save this template.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="rounded-xl border border-border bg-surface p-4">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-foreground">{template.code}</p>
          <p className="text-xs text-foreground/50">
            {template.locale} · {template.is_active ? "active" : "inactive"}
          </p>
        </div>
        <button
          type="button"
          onClick={() => setEditing((v) => !v)}
          className="rounded-full border border-border-strong px-3 py-1 text-xs font-semibold text-foreground/80 hover:bg-surface-hover"
        >
          {editing ? "Close" : "Edit"}
        </button>
      </div>

      {editing && (
        <div className="mt-3 space-y-2">
          <input
            type="text"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            placeholder="Subject"
            className="w-full rounded-lg border border-border-strong bg-surface px-3 py-2 text-sm text-foreground focus:border-teal-400 focus:outline-none"
          />
          <textarea
            value={htmlBody}
            onChange={(e) => setHtmlBody(e.target.value)}
            rows={3}
            placeholder="HTML body"
            className="w-full rounded-lg border border-border-strong bg-surface px-3 py-2 text-sm text-foreground focus:border-teal-400 focus:outline-none"
          />
          <textarea
            value={textBody}
            onChange={(e) => setTextBody(e.target.value)}
            rows={2}
            placeholder="Text body"
            className="w-full rounded-lg border border-border-strong bg-surface px-3 py-2 text-sm text-foreground focus:border-teal-400 focus:outline-none"
          />
          {error && <p className="text-xs text-rose-400">{error}</p>}
          <button
            type="button"
            onClick={handleSave}
            disabled={saving}
            className="rounded-full bg-teal-400 px-3 py-1 text-xs font-semibold text-emerald-950 transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {saving ? "Saving…" : "Save"}
          </button>
        </div>
      )}
    </div>
  );
}
