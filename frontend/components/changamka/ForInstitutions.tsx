import { ArrowRight, Building2, Handshake, Landmark } from "lucide-react";
import { Reveal } from "@/components/animation/Reveal";

const AUDIENCES = [
  {
    icon: Building2,
    title: "Institutional partnerships",
    description: "Offer Changamka to your students through bulk enrollment and institutional programmes.",
  },
  {
    icon: Handshake,
    title: "Corporate sponsorship",
    description: "Sponsor students and build a pipeline of AI-literate future talent.",
  },
  {
    icon: Landmark,
    title: "Government & community programs",
    description: "Support broader digital and AI literacy initiatives through sponsored learning opportunities.",
  },
];

export function ForInstitutions() {
  return (
    <section id="partners" className="scroll-mt-20 bg-surface py-24">
      <div className="mx-auto max-w-7xl px-6">
        <Reveal className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-semibold uppercase tracking-wider text-teal-400">
            For universities, TVETs & organizations
          </p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            Bring Changamka to your students
          </h2>
          <p className="mt-4 text-base leading-7 text-foreground/60">
            Universities, TVET institutions, employers and organizations can partner with
            Changamka to help prepare young people for an AI-powered economy.
          </p>
        </Reveal>

        <Reveal
          className="mx-auto mt-16 grid max-w-2xl grid-cols-1 gap-8 lg:max-w-none lg:grid-cols-3"
          stagger={0.1}
        >
          {AUDIENCES.map(({ icon: Icon, title, description }) => (
            <div key={title} className="rounded-2xl border border-border bg-background p-8">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-teal-500/10 text-teal-400">
                <Icon className="h-5 w-5" strokeWidth={2} />
              </div>
              <h3 className="mt-5 text-lg font-semibold text-foreground">{title}</h3>
              <p className="mt-3 text-sm leading-6 text-foreground/60">{description}</p>
            </div>
          ))}
        </Reveal>

        <Reveal className="mt-12 text-center">
          <a
            href="mailto:info@muiaa.com?subject=Changamka%20partnership%20enquiry"
            className="group inline-flex items-center gap-2 rounded-full bg-foreground px-6 py-3.5 text-sm font-semibold text-background transition-opacity hover:opacity-90"
          >
            Become a partner
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
          </a>
        </Reveal>
      </div>
    </section>
  );
}
