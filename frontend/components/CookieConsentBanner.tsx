"use client";

import { Cookie } from "lucide-react";
import { useSyncExternalStore } from "react";

const STORAGE_KEY = "skillchain.cookie-consent";

const listeners = new Set<() => void>();

function subscribe(callback: () => void) {
  listeners.add(callback);
  return () => listeners.delete(callback);
}

// Whether the banner should be visible — i.e. no stored choice yet. Read
// live from localStorage (like lib/theme/ThemeContext.tsx) rather than
// mirrored into component state, so respond() below can just write storage
// and notify listeners instead of juggling its own "have I dismissed this"
// flag.
function getSnapshot(): boolean {
  try {
    return window.localStorage.getItem(STORAGE_KEY) === null;
  } catch {
    return false;
  }
}

// The server has no access to localStorage, so it always renders the
// banner hidden — same reasoning as ThemeContext's getServerSnapshot.
function getServerSnapshot(): boolean {
  return false;
}

function respond(choice: "accepted" | "declined") {
  try {
    window.localStorage.setItem(STORAGE_KEY, choice);
  } catch {
    // Storage blocked (private browsing, disabled cookies) — the banner
    // will just show again next visit, nothing more we can do.
  }
  listeners.forEach((callback) => callback());
}

export function CookieConsentBanner() {
  const visible = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

  if (!visible) return null;

  return (
    <div className="fixed inset-x-0 bottom-0 z-50 border-t border-border bg-background/95 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl flex-col items-center gap-4 px-6 py-4 sm:flex-row sm:justify-between">
        <div className="flex items-start gap-3 sm:items-center">
          <Cookie className="mt-0.5 h-5 w-5 flex-none text-teal-400 sm:mt-0" />
          <p className="text-sm text-foreground/70">
            We use cookies and similar local storage to keep you signed in, remember your
            preferences, and understand how SkillChain is used.
          </p>
        </div>
        <div className="flex flex-none items-center gap-2">
          <button
            type="button"
            onClick={() => respond("declined")}
            className="rounded-full border border-border-strong px-4 py-2 text-sm font-semibold text-foreground/80 transition-colors hover:bg-surface-hover"
          >
            Decline
          </button>
          <button
            type="button"
            onClick={() => respond("accepted")}
            className="rounded-full bg-teal-400 px-4 py-2 text-sm font-semibold text-emerald-950 transition-opacity hover:opacity-90"
          >
            Accept
          </button>
        </div>
      </div>
    </div>
  );
}
