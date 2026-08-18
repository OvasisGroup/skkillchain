import { ArrowRight } from "lucide-react";
import Link from "next/link";
import { FaqItem } from "@/components/help/FaqItem";
import { Reveal } from "@/components/animation/Reveal";

export const metadata = {
  title: "Help center",
  description:
    "Answers to common questions about enrolling, payments, certificates, live sessions, and becoming an instructor on SkillChain.",
  alternates: { canonical: "/help" },
};

const FAQS = [
  {
    question: "How do I enroll in a course?",
    answer:
      "Browse the course catalog, open a course you're interested in, and select Enroll. Free courses grant access immediately; paid courses take you through checkout first.",
  },
  {
    question: "What payment methods are supported?",
    answer:
      "We support major cards along with regional payment methods including M-Pesa, depending on your location. All payments are processed securely and full card details never touch our servers.",
  },
  {
    question: "How do certificates work?",
    answer:
      "Once you complete all required lessons and assessments in a course, a verifiable certificate is generated automatically and appears on your profile — you can share the link with employers or institutions.",
  },
  {
    question: "Can I join a live session after it starts?",
    answer:
      "Yes, as long as you're registered for the session you can join at any point while it's live from the Live Sessions page or your dashboard.",
  },
  {
    question: "How do I become an instructor?",
    answer:
      "Apply from the For Instructors page with a portfolio or GitHub profile. Our team reviews applications and, once approved, you'll get access to the course builder to publish your first course.",
  },
  {
    question: "How do I reset my password or update my account?",
    answer:
      "Go to Settings from your account menu to update your profile, email, or password. If you're locked out, use the \"Forgot password\" link on the login page.",
  },
];

export default function HelpPage() {
  return (
    <>
      <section className="mx-auto max-w-7xl px-6 py-16 sm:py-24">
        <Reveal className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-semibold uppercase tracking-wider text-lime-400">
            Help center
          </p>
          <h1 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            How can we help?
          </h1>
          <p className="mt-4 text-lg leading-7 text-foreground/60">
            Answers to the questions we hear most. Can&apos;t find yours? Reach out directly.
          </p>
        </Reveal>

        <Reveal className="mx-auto mt-16 max-w-3xl space-y-4" stagger={0.06}>
          {FAQS.map((faq) => (
            <FaqItem key={faq.question} question={faq.question} answer={faq.answer} />
          ))}
        </Reveal>
      </section>

      <section className="mx-auto max-w-7xl px-6 pb-24">
        <Reveal
          y={32}
          className="relative overflow-hidden rounded-3xl bg-teal-600 px-8 py-16 text-center shadow-2xl shadow-teal-900/30 sm:px-16"
        >
          <h2 className="relative mx-auto max-w-2xl text-3xl font-semibold tracking-tight text-white sm:text-4xl">
            Still need help?
          </h2>
          <p className="relative mx-auto mt-4 max-w-xl text-lg text-emerald-50/80">
            Our team is happy to help with anything not covered here.
          </p>
          <div className="relative mt-10 flex flex-wrap items-center justify-center gap-4">
            <Link
              href="/contact"
              className="group inline-flex items-center gap-2 rounded-full bg-white px-6 py-3.5 text-sm font-semibold text-emerald-950 shadow-lg transition-transform hover:scale-[1.02]"
            >
              Contact us
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            </Link>
            <Link
              href="/dashboard/support"
              className="inline-flex items-center gap-2 rounded-full border border-white/30 px-6 py-3.5 text-sm font-semibold text-white transition-colors hover:bg-white/10"
            >
              Open a support ticket
            </Link>
          </div>
        </Reveal>
      </section>
    </>
  );
}
