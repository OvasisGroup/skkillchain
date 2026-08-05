import { Lock, ShieldCheck } from "lucide-react";
import { Reveal } from "@/components/animation/Reveal";

export function Compliance() {
  return (
    <section className="mx-auto max-w-7xl px-6 py-24">
      <Reveal className="mx-auto max-w-2xl text-center">
        <p className="text-sm font-semibold uppercase tracking-wider text-lime-400">
          Compliance & licenses
        </p>
        <h2 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          Data privacy, ethical AI, and legal compliance
        </h2>
      </Reveal>

      <Reveal
        className="mx-auto mt-16 grid max-w-3xl grid-cols-1 gap-6 sm:grid-cols-2"
        stagger={0.1}
      >
        <div className="rounded-2xl border border-dashed border-border-strong p-6">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-teal-500/10 text-teal-400">
            <ShieldCheck className="h-5 w-5" strokeWidth={2} />
          </div>
          <h3 className="mt-5 text-sm font-semibold text-foreground">Licensed under MUIAA Ltd.</h3>
          <ul className="mt-3 space-y-2 text-sm text-foreground/60">
            <li>Kenyan Data Controller License</li>
            <li>Kenyan Data Processor Registration</li>
          </ul>
        </div>

        <div className="rounded-2xl border border-dashed border-border-strong p-6">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-teal-500/10 text-teal-400">
            <Lock className="h-5 w-5" strokeWidth={2} />
          </div>
          <h3 className="mt-5 text-sm font-semibold text-foreground">Adherence to</h3>
          <ul className="mt-3 space-y-2 text-sm text-foreground/60">
            <li>Kenya Data Protection Act, 2019</li>
            <li>EU GDPR standards (for diaspora partnerships)</li>
          </ul>
        </div>
      </Reveal>

      <p className="mx-auto mt-8 max-w-2xl text-center text-sm font-medium text-foreground/50">
        All data is securely stored, encrypted, and never sold.
      </p>
    </section>
  );
}
