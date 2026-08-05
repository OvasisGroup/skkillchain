import type { ReactNode } from "react";
import { Reveal } from "@/components/animation/Reveal";

export function LegalSection({
  id,
  title,
  children,
}: {
  id: string;
  title: string;
  children: ReactNode;
}) {
  return (
    <section id={id} className="scroll-mt-24">
      <Reveal>
        <h2 className="text-lg font-semibold text-foreground">{title}</h2>
        <div className="mt-3 space-y-3 text-sm leading-7 text-foreground/60">
          {children}
        </div>
      </Reveal>
    </section>
  );
}
