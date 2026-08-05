import type { ReactNode } from "react";
import { Reveal } from "@/components/animation/Reveal";

export interface LegalTocItem {
  id: string;
  label: string;
}

export function LegalPage({
  title,
  lastUpdated,
  toc,
  children,
}: {
  title: string;
  lastUpdated: string;
  toc: LegalTocItem[];
  children: ReactNode;
}) {
  return (
    <div className="mx-auto max-w-6xl px-6 py-20">
      <Reveal className="max-w-2xl">
        <p className="text-sm font-semibold uppercase tracking-wider text-lime-400">Legal</p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          {title}
        </h1>
        <p className="mt-3 text-sm text-foreground/40">Last updated {lastUpdated}</p>
      </Reveal>

      <div className="mt-12 grid grid-cols-1 gap-12 lg:grid-cols-[240px_1fr]">
        <nav aria-label="Table of contents" className="hidden lg:block">
          <ul className="sticky top-24 space-y-2 border-l border-border pl-4 text-sm">
            {toc.map((item) => (
              <li key={item.id}>
                <a
                  href={`#${item.id}`}
                  className="text-foreground/50 transition-colors hover:text-teal-400"
                >
                  {item.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>

        <div className="min-w-0 space-y-10">{children}</div>
      </div>
    </div>
  );
}
