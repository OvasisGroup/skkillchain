"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { DashboardShell } from "@/components/dashboard/DashboardShell";
import { LoadingState } from "@/components/dashboard/DashboardStates";
import { useAuth } from "@/lib/auth/AuthContext";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
    }
  }, [isLoading, isAuthenticated, router, pathname]);

  if (isLoading || !isAuthenticated) {
    return (
      <div className="mx-auto max-w-7xl px-6 py-10">
        <LoadingState label="Loading your dashboard…" />
      </div>
    );
  }

  return <DashboardShell>{children}</DashboardShell>;
}
