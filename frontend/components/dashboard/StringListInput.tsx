"use client";

import { Plus, X } from "lucide-react";
import { authInputClass } from "@/components/AuthCard";

export function StringListInput({
  label,
  placeholder,
  values,
  onChange,
}: {
  label: string;
  placeholder: string;
  values: string[];
  onChange: (next: string[]) => void;
}) {
  function update(index: number, value: string) {
    onChange(values.map((v, i) => (i === index ? value : v)));
  }

  function remove(index: number) {
    onChange(values.filter((_, i) => i !== index));
  }

  return (
    <div>
      <span className="block text-sm font-medium text-foreground/70">{label}</span>
      <div className="mt-1.5 space-y-2">
        {values.map((value, index) => (
          <div key={index} className="flex items-center gap-2">
            <input
              type="text"
              value={value}
              onChange={(e) => update(index, e.target.value)}
              placeholder={placeholder}
              className={authInputClass}
            />
            <button
              type="button"
              onClick={() => remove(index)}
              className="rounded-full p-1.5 text-foreground/40 transition-colors hover:bg-surface-hover hover:text-rose-400"
              aria-label={`Remove ${label.toLowerCase()} item`}
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        ))}
        <button
          type="button"
          onClick={() => onChange([...values, ""])}
          className="flex items-center gap-1.5 text-sm font-medium text-teal-400 hover:text-teal-300"
        >
          <Plus className="h-4 w-4" /> Add {label.toLowerCase()}
        </button>
      </div>
    </div>
  );
}
