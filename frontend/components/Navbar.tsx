"use client";

import { Bell, Heart, Menu, ShoppingCart, X } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth/AuthContext";
import { hasRole } from "@/lib/auth/roles";
import { listNotifications } from "@/lib/api/notifications";
import { useCart } from "@/lib/cart/CartContext";
import { ThemeToggle } from "./ThemeToggle";
import { Logo } from "./Logo";
import { UserMenu } from "./UserMenu";

const NAV_LINKS = [
  { href: "/courses", label: "Courses" },
  { href: "/live-sessions", label: "Live Sessions" },
  { href: "/hackathons", label: "Hackathons" },
  { href: "/#for-instructors", label: "For Instructors" },
];

export function Navbar() {
  const [open, setOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const { isAuthenticated, isLoading, user, logout, accessToken } = useAuth();
  const { count: cartCount } = useCart();

  useEffect(() => {
    if (!accessToken) return;
    let cancelled = false;
    listNotifications(accessToken)
      .then((page) => {
        if (!cancelled) setUnreadCount(page.results.filter((n) => !n.read_at).length);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [accessToken]);

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-md">
      <nav className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
        <Logo />

        <div className="hidden items-center gap-8 md:flex">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-sm font-medium text-foreground/60 transition-colors hover:text-foreground"
            >
              {link.label}
            </Link>
          ))}
        </div>

        <div className="hidden items-center gap-3 md:flex">
          <ThemeToggle />
          {!isLoading && isAuthenticated && user ? (
            <>
              <Link
                href="/cart"
                aria-label="Cart"
                className="relative rounded-full p-2 text-foreground/70 transition-colors hover:bg-surface-hover hover:text-foreground"
              >
                <ShoppingCart className="h-5 w-5" />
                {cartCount > 0 && (
                  <span className="absolute right-0.5 top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-teal-400 px-1 text-[10px] font-semibold text-emerald-950">
                    {cartCount}
                  </span>
                )}
              </Link>
              <Link
                href="/wishlist"
                aria-label="Wishlist"
                className="rounded-full p-2 text-foreground/70 transition-colors hover:bg-surface-hover hover:text-foreground"
              >
                <Heart className="h-5 w-5" />
              </Link>
              <Link
                href="/notifications"
                aria-label="Notifications"
                className="relative rounded-full p-2 text-foreground/70 transition-colors hover:bg-surface-hover hover:text-foreground"
              >
                <Bell className="h-5 w-5" />
                {unreadCount > 0 && (
                  <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-rose-500" />
                )}
              </Link>
              <UserMenu user={user} onLogout={() => logout()} />
            </>
          ) : (
            <>
              <Link
                href="/login"
                className="text-sm font-medium text-foreground/70 hover:text-foreground"
              >
                Log in
              </Link>
              <Link
                href="/register"
                className="rounded-full bg-teal-400 px-5 py-2 text-sm font-semibold text-emerald-950 shadow-sm shadow-teal-500/20 transition-opacity hover:opacity-90"
              >
                Get started free
              </Link>
            </>
          )}
        </div>

        <div className="flex items-center gap-2 md:hidden">
          <ThemeToggle />
          <button
            className="p-2 text-foreground/80"
            onClick={() => setOpen((o) => !o)}
            aria-label="Toggle menu"
          >
            {open ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>
      </nav>

      {open && (
        <div className="border-t border-border bg-background px-6 py-4 md:hidden">
          <div className="flex flex-col gap-4">
            {NAV_LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setOpen(false)}
                className="text-sm font-medium text-foreground/80"
              >
                {link.label}
              </Link>
            ))}
            <hr className="border-border" />
            {!isLoading && isAuthenticated && user ? (
              <>
                <Link
                  href="/dashboard"
                  onClick={() => setOpen(false)}
                  className="text-sm font-medium text-foreground/80"
                >
                  Dashboard
                </Link>
                <Link
                  href="/cart"
                  onClick={() => setOpen(false)}
                  className="text-sm font-medium text-foreground/80"
                >
                  Cart{cartCount > 0 ? ` (${cartCount})` : ""}
                </Link>
                <Link
                  href="/wishlist"
                  onClick={() => setOpen(false)}
                  className="text-sm font-medium text-foreground/80"
                >
                  Wishlist
                </Link>
                <Link
                  href="/notifications"
                  onClick={() => setOpen(false)}
                  className="text-sm font-medium text-foreground/80"
                >
                  Notifications{unreadCount > 0 ? ` (${unreadCount})` : ""}
                </Link>
                <Link
                  href="/profile"
                  onClick={() => setOpen(false)}
                  className="text-sm font-medium text-foreground/80"
                >
                  Profile
                </Link>
                <Link
                  href="/settings"
                  onClick={() => setOpen(false)}
                  className="text-sm font-medium text-foreground/80"
                >
                  Settings
                </Link>
                <Link
                  href="/dashboard/affiliate"
                  onClick={() => setOpen(false)}
                  className="text-sm font-medium text-foreground/80"
                >
                  Affiliate
                </Link>
                <Link
                  href="/dashboard/instructor"
                  onClick={() => setOpen(false)}
                  className="text-sm font-medium text-foreground/80"
                >
                  {hasRole(user, "instructor") ? "Instructor dashboard" : "Join as instructor"}
                </Link>
                <button
                  onClick={() => logout()}
                  className="text-left text-sm font-medium text-foreground/80"
                >
                  Log out
                </button>
              </>
            ) : (
              <>
                <Link href="/login" onClick={() => setOpen(false)} className="text-sm font-medium text-foreground/80">
                  Log in
                </Link>
                <Link
                  href="/register"
                  onClick={() => setOpen(false)}
                  className="rounded-full bg-teal-400 px-5 py-2 text-center text-sm font-semibold text-emerald-950"
                >
                  Get started free
                </Link>
              </>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
