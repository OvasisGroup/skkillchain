import Link from "next/link";
import { LegalPage } from "@/components/legal/LegalPage";
import { LegalSection } from "@/components/legal/LegalSection";

export const metadata = {
  title: "Privacy Policy",
  description: "How SkillChain collects, uses, and protects your data.",
  alternates: { canonical: "/privacy" },
};

const TOC = [
  { id: "overview", label: "1. Overview & scope" },
  { id: "controller", label: "2. Data controller" },
  { id: "collect", label: "3. Information we collect" },
  { id: "use", label: "4. How we use your information" },
  { id: "legal-basis", label: "5. Legal basis for processing" },
  { id: "cookies", label: "6. Cookies & local storage" },
  { id: "sharing", label: "7. How we share information" },
  { id: "security", label: "8. Data storage & security" },
  { id: "transfers", label: "9. International transfers" },
  { id: "retention", label: "10. Data retention" },
  { id: "rights", label: "11. Your rights" },
  { id: "children", label: "12. Children's privacy" },
  { id: "changes", label: "13. Changes to this policy" },
  { id: "contact", label: "14. Contact us" },
];

export default function PrivacyPage() {
  return (
    <LegalPage title="Privacy Policy" lastUpdated="July 31, 2026" toc={TOC}>
      <LegalSection id="overview" title="1. Overview & scope">
        <p>
          This Privacy Policy explains how MUIAA Ltd, trading as SkillChain
          (&quot;SkillChain&quot;, &quot;we&quot;, &quot;us&quot;), collects, uses, shares, and
          protects information when you use our website, APIs, and related services (the
          &quot;Service&quot;). It applies to students, instructors, affiliates, and any other
          visitor to SkillChain. It should be read together with our{" "}
          <Link href="/terms" className="text-teal-400 hover:underline">
            Terms of Service
          </Link>
          .
        </p>
      </LegalSection>

      <LegalSection id="controller" title="2. Data controller">
        <p>
          MUIAA Ltd is the data controller responsible for your information under this policy. We
          are registered as a data controller and data processor in Kenya, and we design our data
          practices to meet the requirements of the Kenya Data Protection Act, 2019, and — for
          learners and partners connecting from the EU — the EU General Data Protection
          Regulation (GDPR).
        </p>
      </LegalSection>

      <LegalSection id="collect" title="3. Information we collect">
        <ul className="list-disc space-y-2 pl-5 marker:text-teal-400">
          <li>
            <span className="font-medium text-foreground/80">Account & profile —</span> name,
            email, password (stored as a salted hash), profile bio, avatar, locale, timezone, and
            any social links you add.
          </li>
          <li>
            <span className="font-medium text-foreground/80">Course activity —</span> enrollments,
            lesson progress, quiz and assignment submissions, coding-exercise attempts, reviews,
            and discussion posts.
          </li>
          <li>
            <span className="font-medium text-foreground/80">Live sessions —</span> registration
            and attendance records, and — only for instructors who connect one — an encrypted
            OAuth token for your Zoom or Google Meet account, used solely to create and manage
            sessions you schedule.
          </li>
          <li>
            <span className="font-medium text-foreground/80">Payments —</span> order and
            transaction records (amount, currency, status, payment method type). Full card numbers
            and mobile-money PINs are handled by our payment processors and never touch our
            servers.
          </li>
          <li>
            <span className="font-medium text-foreground/80">Support —</span> the content of
            support tickets and messages you send us.
          </li>
          <li>
            <span className="font-medium text-foreground/80">Device & usage data —</span> IP
            address, browser type, and pages visited, collected automatically to keep the Service
            secure and to understand how it&apos;s used.
          </li>
          <li>
            <span className="font-medium text-foreground/80">Cookies & local storage —</span> see
            Section 6.
          </li>
        </ul>
      </LegalSection>

      <LegalSection id="use" title="4. How we use your information">
        <ul className="list-disc space-y-2 pl-5 marker:text-teal-400">
          <li>Operate and maintain your account, and deliver course content and certificates.</li>
          <li>Process payments, payouts, coupons, and affiliate commissions.</li>
          <li>Send transactional emails and notifications (enrollment, grading, live-session reminders, support replies).</li>
          <li>Provide AI-tutor responses, summaries, and grading suggestions.</li>
          <li>Maintain audit logs of access-denied and administrative actions for security and accountability.</li>
          <li>Detect and prevent fraud, abuse, and violations of our Terms.</li>
          <li>Comply with legal obligations, including tax and consumer-protection law.</li>
        </ul>
        <p>We do not sell your personal data to third parties.</p>
      </LegalSection>

      <LegalSection id="legal-basis" title="5. Legal basis for processing">
        <p>
          Where the GDPR or the Kenya Data Protection Act applies, we rely on one or more of the
          following bases: performance of a contract with you (running your account and
          delivering courses you enrolled in), your consent (for example, optional marketing
          communications or connecting a conferencing account), our legitimate interests (security,
          fraud prevention, improving the Service), and compliance with a legal obligation (such
          as retaining financial records).
        </p>
      </LegalSection>

      <LegalSection id="cookies" title="6. Cookies & local storage">
        <p>
          We use cookies and browser local storage to keep you signed in, remember your theme and
          cart, and understand aggregate usage of the Service. You can decline non-essential
          storage from the cookie banner shown on your first visit; essential storage needed to
          keep you logged in and operate the Service cannot be disabled without affecting
          functionality. You can also clear cookies and local storage at any time through your
          browser settings.
        </p>
      </LegalSection>

      <LegalSection id="sharing" title="7. How we share information">
        <p>We share information only where necessary to operate the Service:</p>
        <ul className="list-disc space-y-2 pl-5 marker:text-teal-400">
          <li>
            <span className="font-medium text-foreground/80">Payment processors —</span> Stripe,
            PayPal, Flutterwave, Paystack, and M-Pesa, to process payments and payouts.
          </li>
          <li>
            <span className="font-medium text-foreground/80">Conferencing providers —</span> Zoom
            and Google Meet, only for live sessions you register for or host.
          </li>
          <li>
            <span className="font-medium text-foreground/80">Communications providers —</span>{" "}
            email and SMS delivery services, to send notifications you&apos;re entitled to
            receive.
          </li>
          <li>
            <span className="font-medium text-foreground/80">Instructors —</span> your name and
            submitted work, limited to courses you&apos;re enrolled in, so they can grade and
            respond to you.
          </li>
          <li>
            <span className="font-medium text-foreground/80">Legal & safety —</span> where required
            by law, regulation, or a valid legal process, or to protect the rights and safety of
            SkillChain, our users, or the public.
          </li>
        </ul>
        <p>We do not sell or rent your personal data.</p>
      </LegalSection>

      <LegalSection id="security" title="8. Data storage & security">
        <p>
          We use industry-standard safeguards to protect your data, including encryption of
          sensitive credentials such as conferencing OAuth tokens, access controls limiting who on
          our team can view personal data, and audit logging of sensitive actions. No method of
          transmission or storage is 100% secure, but we work to protect your information and to
          respond quickly if something goes wrong.
        </p>
      </LegalSection>

      <LegalSection id="transfers" title="9. International transfers">
        <p>
          SkillChain is based in Kenya, and some of our processors and partners — including
          diaspora and international partnerships — operate outside Kenya, including in the EU
          and the US. Where we transfer personal data internationally, we take steps consistent
          with the Kenya Data Protection Act and, where applicable, GDPR safeguards for
          cross-border transfers.
        </p>
      </LegalSection>

      <LegalSection id="retention" title="10. Data retention">
        <p>
          We retain your information for as long as your account is active and as needed to
          provide the Service, plus any additional period required to meet legal, tax, or
          accounting obligations, resolve disputes, and enforce our agreements. Certificate
          records are retained indefinitely so verification links continue to work after you close
          your account.
        </p>
      </LegalSection>

      <LegalSection id="rights" title="11. Your rights">
        <p>
          Subject to applicable law, you have the right to access the personal data we hold about
          you, correct inaccurate data, request deletion, object to or restrict certain
          processing, and receive a copy of your data in a portable format. You can update most
          profile information directly from your account settings, or contact us at{" "}
          <a href="mailto:contact@skillchain.com" className="text-teal-400 hover:underline">
            contact@skillchain.com
          </a>{" "}
          to exercise these rights. If you&apos;re not satisfied with our response, you may lodge
          a complaint with Kenya&apos;s Office of the Data Protection Commissioner (ODPC) or, if
          the GDPR applies to you, your local data protection authority.
        </p>
      </LegalSection>

      <LegalSection id="children" title="12. Children's privacy">
        <p>
          SkillChain is not directed at children under 16. If you are between 16 and the age of
          majority in your jurisdiction, you may only use the Service with a parent or
          guardian&apos;s consent. If we learn we&apos;ve collected personal data from a child
          without appropriate consent, we will delete it.
        </p>
      </LegalSection>

      <LegalSection id="changes" title="13. Changes to this policy">
        <p>
          We may update this Privacy Policy from time to time. If a change is material, we&apos;ll
          notify you by email or an in-app notice before it takes effect. The &quot;Last
          updated&quot; date at the top of this page reflects the most recent revision.
        </p>
      </LegalSection>

      <LegalSection id="contact" title="14. Contact us">
        <p>For privacy questions, data requests, or to reach our data protection contact:</p>
        <p>
          MUIAA Ltd, trading as SkillChain
          <br />
          Nairobi, Kenya
          <br />
          <a href="mailto:contact@skillchain.com" className="text-teal-400 hover:underline">
            contact@skillchain.com
          </a>
          <br />
          <a href="tel:+254718540760" className="text-teal-400 hover:underline">
            +254 718 540 760
          </a>
        </p>
      </LegalSection>
    </LegalPage>
  );
}
