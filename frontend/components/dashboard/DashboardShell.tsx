"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth/AuthContext";
import { DASHBOARD_NAV } from "@/lib/auth/roles";

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user } = useAuth();
  const items = DASHBOARD_NAV.filter((item) => item.visible(user));

  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-6 px-4 py-8 sm:px-6 lg:flex-row lg:gap-8 lg:py-10">
      <aside className="lg:w-60 lg:flex-none">
        <nav className="flex gap-1 overflow-x-auto pb-1 lg:sticky lg:top-24 lg:flex-col lg:gap-1 lg:overflow-visible lg:pb-0">
          {items.map((item) => {
            const active = pathname === item.path || pathname?.startsWith(`${item.path}/`);
            const Icon = item.icon;
            return (
              <Link
                key={item.path}
                href={item.path}
                aria-current={active ? "page" : undefined}
                className={`group relative flex flex-none items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors ${
                  active
                    ? "bg-teal-400/10 text-teal-400"
                    : "text-foreground/50 hover:bg-surface-hover hover:text-foreground"
                }`}
              >
                <span
                  className={`absolute left-0 top-1/2 hidden h-5 w-0.5 -translate-y-1/2 rounded-full bg-teal-400 transition-opacity lg:block ${
                    active ? "opacity-100" : "opacity-0"
                  }`}
                />
                <Icon className="h-5 w-5 flex-none" strokeWidth={active ? 2.25 : 1.75} />
                <span className="whitespace-nowrap">{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </aside>
      <main className="min-w-0 flex-1">{children}</main>
    </div>
  );
}
