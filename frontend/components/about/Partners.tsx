import { CheckCircle2, Handshake } from "lucide-react";
import { Reveal } from "@/components/animation/Reveal";

const PARTNERS = [
  "Nairobi County",
  "Digital Economy & Startups Department (ICT Authority)",
  "Computer Aid International",
  "Cypherium (Hybrid Blockchain)",
];

const ACHIEVEMENTS = ["Certificates issued", "Projects launched", "Developers hired"];

export function Partners() {
  return (
    <section className="bg-surface py-24">
      <div className="mx-auto max-w-7xl px-6">
        <Reveal className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-semibold uppercase tracking-wider text-lime-400">
            Our partners
          </p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            Backed by government, NGO, and industry partners
          </h2>
          <p className="mt-4 text-lg text-foreground/60">
            Our hackathons and bootcamps are hosted together with organizations already investing
            in Kenya&apos;s digital economy.
          </p>
        </Reveal>

        <Reveal
          className="mx-auto mt-12 flex max-w-4xl flex-wrap items-center justify-center gap-3"
          stagger={0.08}
        >
          {PARTNERS.map((partner) => (
            <span
              key={partner}
              className="flex items-center gap-2 rounded-full border border-border-strong bg-background px-4 py-2 text-sm font-medium text-foreground/80"
            >
              <Handshake className="h-4 w-4 text-teal-400" />
              {partner}
            </span>
          ))}
        </Reveal>

        <div className="mx-auto mt-10 flex max-w-xl flex-wrap items-center justify-center gap-x-8 gap-y-3">
          {ACHIEVEMENTS.map((achievement) => (
            <span
              key={achievement}
              className="flex items-center gap-2 text-sm font-medium text-foreground/70"
            >
              <CheckCircle2 className="h-4 w-4 text-emerald-400" />
              {achievement}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}
