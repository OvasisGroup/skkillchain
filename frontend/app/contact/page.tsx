import { ArrowRight, Mail, MapPin, MessageCircle, Phone } from "lucide-react";
import Link from "next/link";
import { Reveal } from "@/components/animation/Reveal";

export const metadata = {
  title: "Contact us",
  description:
    "Get in touch with the SkillChain team — email, call, or open a support ticket for account and course issues.",
  alternates: { canonical: "/contact" },
};

const CHANNELS = [
  {
    icon: Mail,
    title: "Email us",
    detail: "contact@skillchain.com",
    href: "mailto:contact@skillchain.com",
  },
  {
    icon: Phone,
    title: "Call us",
    detail: "+254 718 540 760",
    href: "tel:+254718540760",
  },
  {
    icon: MapPin,
    title: "Visit us",
    detail: "Nairobi, Kenya",
    href: null,
  },
];

export default function ContactPage() {
  return (
    <>
      <section className="mx-auto max-w-7xl px-6 py-16 sm:py-24">
        <Reveal className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-semibold uppercase tracking-wider text-lime-400">
            Contact us
          </p>
          <h1 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            We&apos;d love to hear from you
          </h1>
          <p className="mt-4 text-lg leading-7 text-foreground/60">
            Questions about a course, a payment, or partnering with SkillChain? Reach us directly,
            or open a support ticket if you have an account issue.
          </p>
        </Reveal>

        <Reveal
          className="mx-auto mt-16 grid max-w-2xl grid-cols-1 gap-6 sm:grid-cols-3 lg:max-w-none"
          stagger={0.1}
        >
          {CHANNELS.map(({ icon: Icon, title, detail, href }) => {
            const content = (
              <>
                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-teal-500/10 text-teal-400">
                  <Icon className="h-5 w-5" strokeWidth={2} />
                </div>
                <h3 className="mt-5 text-base font-semibold text-foreground">{title}</h3>
                <p className="mt-2 text-sm text-foreground/60">{detail}</p>
              </>
            );

            return href ? (
              <a
                key={title}
                href={href}
                className="group rounded-2xl border border-border bg-surface p-6 transition-colors hover:border-teal-400/30 hover:bg-surface-hover"
              >
                {content}
              </a>
            ) : (
              <div key={title} className="rounded-2xl border border-border bg-surface p-6">
                {content}
              </div>
            );
          })}
        </Reveal>
      </section>

      <section className="mx-auto max-w-7xl px-6 pb-24">
        <Reveal
          y={32}
          className="relative overflow-hidden rounded-3xl bg-teal-600 px-8 py-16 text-center shadow-2xl shadow-teal-900/30 sm:px-16"
        >
          <MessageCircle className="mx-auto h-8 w-8 text-white/70" strokeWidth={1.5} />
          <h2 className="relative mx-auto mt-4 max-w-2xl text-3xl font-semibold tracking-tight text-white sm:text-4xl">
            Already have an account?
          </h2>
          <p className="relative mx-auto mt-4 max-w-xl text-lg text-emerald-50/80">
            Open a support ticket and our team will follow up directly in your dashboard.
          </p>
          <div className="relative mt-10 flex flex-wrap items-center justify-center gap-4">
            <Link
              href="/dashboard/support"
              className="group inline-flex items-center gap-2 rounded-full bg-white px-6 py-3.5 text-sm font-semibold text-emerald-950 shadow-lg transition-transform hover:scale-[1.02]"
            >
              Open a support ticket
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            </Link>
            <Link
              href="/help"
              className="inline-flex items-center gap-2 rounded-full border border-white/30 px-6 py-3.5 text-sm font-semibold text-white transition-colors hover:bg-white/10"
            >
              Visit the help center
            </Link>
          </div>
        </Reveal>
      </section>
    </>
  );
}
