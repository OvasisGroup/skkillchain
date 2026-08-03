import { CodeXml } from "lucide-react";
import Link from "next/link";

export function Logo({ className = "" }: { className?: string }) {
  return (
    <Link href="/" className={`flex items-center gap-2 font-semibold tracking-tight ${className}`}>
      <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-teal-400 text-emerald-950 shadow-sm shadow-teal-500/30">
        <CodeXml className="h-5 w-5" strokeWidth={2.5} />
      </span>
      <span className="text-lg text-foreground">SkillChain</span>
    </Link>
  );
}
