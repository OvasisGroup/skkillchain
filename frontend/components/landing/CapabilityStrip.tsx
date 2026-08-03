import {
  Award,
  CreditCard,
  MessagesSquare,
  ShieldCheck,
  Sparkles,
  Video,
} from "lucide-react";

const CAPABILITIES = [
  { icon: Video, label: "Live sessions" },
  { icon: Sparkles, label: "AI-powered tutor" },
  { icon: Award, label: "Verified certificates" },
  { icon: MessagesSquare, label: "Real-time messaging" },
  { icon: CreditCard, label: "Secure payments" },
  { icon: ShieldCheck, label: "Role-based access control" },
];

export function CapabilityStrip() {
  return (
    <section className="border-y border-border bg-surface">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-center gap-x-10 gap-y-6 px-6 py-8">
        {CAPABILITIES.map(({ icon: Icon, label }) => (
          <div
            key={label}
            className="flex items-center gap-2 text-sm font-medium text-foreground/60"
          >
            <Icon className="h-4 w-4 text-teal-400" />
            {label}
          </div>
        ))}
      </div>
    </section>
  );
}
