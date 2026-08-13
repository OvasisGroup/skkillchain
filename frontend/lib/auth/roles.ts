import {
  Banknote,
  BookOpen,
  Building2,
  FileCheck2,
  GraduationCap,
  LifeBuoy,
  Link2,
  type LucideIcon,
  ShieldAlert,
  ShieldCheck,
  Trophy,
} from "lucide-react";
import type { Me, RoleCode } from "@/lib/api/types";

export function hasRole(user: Me | null, ...codes: RoleCode[]): boolean {
  if (!user) return false;
  return codes.some((code) => user.roles.includes(code));
}

// Admins hold every admin-style permission (every RolePermission seed
// migration grants administrator + super_administrator alongside the
// specialized role) so they see every specialized dashboard too, rather
// than duplicating those pages inside a separate "admin" catch-all.
export function isAdmin(user: Me | null): boolean {
  return hasRole(user, "administrator", "super_administrator");
}

export interface DashboardNavItem {
  path: string;
  label: string;
  icon: LucideIcon;
  visible: (user: Me | null) => boolean;
}

// Student/Instructor/Affiliate/Organization have no in-app role-assignment
// step (instructor and affiliate are both self-service "apply/register"
// flows; organization is a future capability with nothing to gate) so they
// stay visible to every authenticated user — the page itself renders an
// apply/register CTA when the user doesn't have full access yet. The
// admin-style roles below are never self-service (no role-assignment
// endpoint exists anywhere in the API), so they're hidden unless the user
// already holds the role.
export const DASHBOARD_NAV: DashboardNavItem[] = [
  { path: "/dashboard/student", label: "Student", icon: GraduationCap, visible: () => true },
  { path: "/dashboard/instructor", label: "Instructor", icon: BookOpen, visible: () => true },
  { path: "/dashboard/hackathons", label: "Hackathons", icon: Trophy, visible: () => true },
  {
    path: "/dashboard/moderator",
    label: "Moderator",
    icon: ShieldCheck,
    visible: (u) => hasRole(u, "moderator") || isAdmin(u),
  },
  {
    path: "/dashboard/content-reviewer",
    label: "Content Reviewer",
    icon: FileCheck2,
    visible: (u) => hasRole(u, "content_reviewer") || isAdmin(u),
  },
  {
    path: "/dashboard/support",
    label: "Support",
    icon: LifeBuoy,
    visible: (u) => hasRole(u, "support_agent") || isAdmin(u),
  },
  {
    path: "/dashboard/finance",
    label: "Finance",
    icon: Banknote,
    visible: (u) => hasRole(u, "finance_officer") || isAdmin(u),
  },
  { path: "/dashboard/affiliate", label: "Affiliate", icon: Link2, visible: () => true },
  { path: "/dashboard/admin", label: "Admin", icon: ShieldAlert, visible: (u) => isAdmin(u) },
  {
    path: "/dashboard/organization",
    label: "Organization",
    icon: Building2,
    visible: () => true,
  },
];

const PRIMARY_PRIORITY: { path: string; test: (user: Me) => boolean }[] = [
  { path: "/dashboard/admin", test: isAdmin },
  { path: "/dashboard/moderator", test: (u) => hasRole(u, "moderator") },
  { path: "/dashboard/content-reviewer", test: (u) => hasRole(u, "content_reviewer") },
  { path: "/dashboard/support", test: (u) => hasRole(u, "support_agent") },
  { path: "/dashboard/finance", test: (u) => hasRole(u, "finance_officer") },
  { path: "/dashboard/instructor", test: (u) => hasRole(u, "instructor") },
];

export function primaryDashboardPath(user: Me | null): string {
  if (!user) return "/dashboard/student";
  return PRIMARY_PRIORITY.find((p) => p.test(user))?.path ?? "/dashboard/student";
}

// A `?next=` value comes straight from the URL, so it's attacker-controlled
// (e.g. a phishing link with `?next=https://evil.example/login`). Only
// accept a same-site relative path — a single leading `/` and not `//`,
// since `//host` is parsed by browsers as a protocol-relative URL and
// escapes the site just like an absolute one.
export function safeRedirectPath(next: string | null, fallback: string): string {
  if (next && next.startsWith("/") && !next.startsWith("//")) {
    return next;
  }
  return fallback;
}
