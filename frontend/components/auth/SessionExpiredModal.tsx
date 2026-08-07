"use client";

import { AlertTriangle } from "lucide-react";

interface SessionExpiredModalProps {
  open: boolean;
  onContinue: () => void;
  onCancel: () => void;
}

// Intentionally has no backdrop-click/Escape dismissal — the session is
// already expired server-side, so "close without choosing" isn't a valid
// third option; the user must pick Continue or Cancel.
export function SessionExpiredModal({ open, onContinue, onCancel }: SessionExpiredModalProps) {
  if (!open) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="session-expired-title"
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 px-4"
    >
      <div className="w-full max-w-sm rounded-2xl border border-border bg-surface p-6 text-center shadow-xl">
        <AlertTriangle className="mx-auto h-8 w-8 text-amber-400" />
        <h2 id="session-expired-title" className="mt-4 text-lg font-semibold text-foreground">
          Your session has expired
        </h2>
        <p className="mt-2 text-sm text-foreground/60">
          Continue to sign back in, or cancel to return to the homepage.
        </p>
        <div className="mt-6 flex gap-3">
          <button
            type="button"
            onClick={onCancel}
            className="flex-1 rounded-full border border-border-strong px-4 py-2.5 text-sm font-medium text-foreground/80 transition-colors hover:bg-surface-hover"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onContinue}
            className="flex-1 rounded-full bg-teal-400 px-4 py-2.5 text-sm font-semibold text-emerald-950 transition-opacity hover:opacity-90"
          >
            Continue
          </button>
        </div>
      </div>
    </div>
  );
}
