import {
  Award,
  CreditCard,
  ShieldCheck,
  Video,
} from "lucide-react";
import { Reveal } from "@/components/animation/Reveal";

const CAPABILITIES = [
  { icon: Video, label: "Live sessions" },
  { icon: Award, label: "Verified certificates" },
  { icon: CreditCard, label: "Secure payments" },
  { icon: ShieldCheck, label: "Role-based access control" },
];

export function CapabilityStrip() {
  return (
    <section className="bg-teal-600">
      <Reveal
        className="mx-auto flex max-w-7xl flex-col items-center gap-y-1.5 px-6 py-8 sm:flex-row sm:flex-wrap sm:justify-center sm:gap-x-10 sm:gap-y-6"
        stagger={0.08}
        y={12}
      >
        {CAPABILITIES.map(({ icon: Icon, label }) => (
          <div
            key={label}
            className="flex items-center gap-2 text-sm font-medium text-white/90"
          >
            <Icon className="hidden h-4 w-4 text-black sm:block" />
            {label}
          </div>
        ))}
      </Reveal>
    </section>
  );
}
