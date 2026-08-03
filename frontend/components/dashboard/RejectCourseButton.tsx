"use client";

import { useState } from "react";

export function RejectCourseButton({
  onReject,
  busy,
}: {
  onReject: (reason: string) => void;
  busy: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState("");

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="rounded-full border border-rose-500/30 px-3 py-1 text-xs font-semibold text-rose-400 transition-colors hover:bg-rose-500/10"
      >
        Reject
      </button>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <input
        type="text"
        value={reason}
        onChange={(e) => setReason(e.target.value)}
        placeholder="Reason for rejection"
        className="w-48 rounded-lg border border-border-strong bg-surface px-2 py-1 text-xs text-foreground focus:border-teal-400 focus:outline-none"
      />
      <button
        type="button"
        disabled={busy || !reason.trim()}
        onClick={() => onReject(reason)}
        className="rounded-full bg-rose-500 px-3 py-1 text-xs font-semibold text-white transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
      >
        Confirm
      </button>
      <button
        type="button"
        onClick={() => setOpen(false)}
        className="text-xs text-foreground/50 hover:text-foreground"
      >
        Cancel
      </button>
    </div>
  );
}
