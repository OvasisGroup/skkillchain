"use client";

import { ChevronDown } from "lucide-react";
import { useState } from "react";

export function FaqItem({ question, answer }: { question: string; answer: string }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="rounded-2xl border border-border bg-surface">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        className="flex w-full items-center justify-between gap-4 px-6 py-5 text-left"
      >
        <span className="text-sm font-semibold text-foreground">{question}</span>
        <ChevronDown
          className={`h-4 w-4 flex-none text-foreground/40 transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>
      {open && (
        <p className="px-6 pb-5 text-sm leading-6 text-foreground/60">{answer}</p>
      )}
    </div>
  );
}
