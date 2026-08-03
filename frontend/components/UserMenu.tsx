"use client";

import { BadgeCheck, ChevronDown, LayoutDashboard, Link2, LogOut, Settings, User as UserIcon } from "lucide-react";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import type { Me } from "@/lib/api/types";
import { hasRole } from "@/lib/auth/roles";

export function UserMenu({ user, onLogout }: { user: Me; onLogout: () => void }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const isInstructor = hasRole(user, "instructor");
  const displayName = user.profile.first_name || user.email;

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="menu"
        aria-expanded={open}
        className="flex items-center gap-2 rounded-full border border-border-strong py-1 pl-1 pr-2.5 text-sm font-medium text-foreground/80 transition-colors hover:bg-surface-hover"
      >
        <span className="flex h-7 w-7 flex-none items-center justify-center rounded-full bg-teal-400 text-xs font-semibold text-emerald-950">
          {displayName.charAt(0).toUpperCase()}
        </span>
        <span className="max-w-[9rem] truncate">{displayName}</span>
        <ChevronDown className={`h-4 w-4 flex-none text-foreground/50 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>

      {open && (
        <div
          role="menu"
          className="absolute right-0 top-full z-50 mt-2 w-56 overflow-hidden rounded-xl border border-border bg-surface py-1 shadow-lg"
        >
          <Link
            href="/dashboard"
            role="menuitem"
            onClick={() => setOpen(false)}
            className="flex items-center gap-2.5 px-4 py-2.5 text-sm text-foreground/80 hover:bg-surface-hover hover:text-foreground"
          >
            <LayoutDashboard className="h-4 w-4" />
            Dashboard
          </Link>
          <Link
            href="/profile"
            role="menuitem"
            onClick={() => setOpen(false)}
            className="flex items-center gap-2.5 px-4 py-2.5 text-sm text-foreground/80 hover:bg-surface-hover hover:text-foreground"
          >
            <UserIcon className="h-4 w-4" />
            Profile
          </Link>
          <Link
            href="/settings"
            role="menuitem"
            onClick={() => setOpen(false)}
            className="flex items-center gap-2.5 px-4 py-2.5 text-sm text-foreground/80 hover:bg-surface-hover hover:text-foreground"
          >
            <Settings className="h-4 w-4" />
            Settings
          </Link>
          <Link
            href="/dashboard/affiliate"
            role="menuitem"
            onClick={() => setOpen(false)}
            className="flex items-center gap-2.5 px-4 py-2.5 text-sm text-foreground/80 hover:bg-surface-hover hover:text-foreground"
          >
            <Link2 className="h-4 w-4" />
            Affiliate
          </Link>
          <Link
            href="/dashboard/instructor"
            role="menuitem"
            onClick={() => setOpen(false)}
            className="flex items-center gap-2.5 px-4 py-2.5 text-sm text-foreground/80 hover:bg-surface-hover hover:text-foreground"
          >
            <BadgeCheck className="h-4 w-4" />
            {isInstructor ? "Instructor dashboard" : "Join as instructor"}
          </Link>
          <hr className="my-1 border-border" />
          <button
            type="button"
            role="menuitem"
            onClick={() => {
              setOpen(false);
              onLogout();
            }}
            className="flex w-full items-center gap-2.5 px-4 py-2.5 text-left text-sm text-foreground/80 hover:bg-surface-hover hover:text-foreground"
          >
            <LogOut className="h-4 w-4" />
            Log out
          </button>
        </div>
      )}
    </div>
  );
}
