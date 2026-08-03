import { Building2 } from "lucide-react";

export default function OrganizationDashboardPage() {
  return (
    <div className="rounded-2xl border border-border bg-surface p-8 text-center">
      <Building2 className="mx-auto h-8 w-8 text-teal-400" />
      <h1 className="mt-4 text-xl font-semibold text-foreground">Organization accounts are coming soon</h1>
      <p className="mx-auto mt-2 max-w-md text-sm text-foreground/60">
        Team seat management, bulk enrollment, and organization-level reporting are on our
        roadmap. Check back soon.
      </p>
    </div>
  );
}
