import type { LucideIcon } from "lucide-react";

export function StatCard({
  label,
  value,
  sublabel,
  icon: Icon,
}: {
  label: string;
  value: string;
  sublabel?: string;
  icon?: LucideIcon;
}) {
  return (
    <div className="group rounded-2xl border border-border bg-surface p-5 transition-colors hover:border-teal-400/30">
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium uppercase tracking-wide text-foreground/50">{label}</p>
        {Icon && (
          <span className="flex h-8 w-8 flex-none items-center justify-center rounded-full bg-teal-400/10 text-teal-400 transition-colors group-hover:bg-teal-400/20">
            <Icon className="h-4 w-4" />
          </span>
        )}
      </div>
      <p className="mt-3 text-2xl font-semibold tracking-tight text-foreground">{value}</p>
      {sublabel && <p className="mt-1 text-xs text-foreground/40">{sublabel}</p>}
    </div>
  );
}
