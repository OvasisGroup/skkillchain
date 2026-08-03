"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { LoadingState } from "@/components/dashboard/DashboardStates";
import { useAuth } from "@/lib/auth/AuthContext";
import { primaryDashboardPath } from "@/lib/auth/roles";

export default function DashboardIndexPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && user) {
      router.replace(primaryDashboardPath(user));
    }
  }, [isLoading, user, router]);

  return <LoadingState label="Redirecting to your dashboard…" />;
}
