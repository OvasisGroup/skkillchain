import Link from "next/link";
import { LegalPage } from "@/components/legal/LegalPage";
import { LegalSection } from "@/components/legal/LegalSection";

export const metadata = {
  title: "Terms of Service",
  description: "The terms that govern your use of SkillChain.",
  alternates: { canonical: "/terms" },
};

const TOC = [
  { id: "acceptance", label: "1. Acceptance of terms" },
  { id: "service", label: "2. Description of service" },
  { id: "accounts", label: "3. Eligibility & accounts" },
  { id: "roles", label: "4. Account roles" },
  { id: "instructors", label: "5. Instructor terms" },
  { id: "payments", label: "6. Payments, pricing & refunds" },
  { id: "live-sessions", label: "7. Live sessions" },
  { id: "conduct", label: "8. Community guidelines" },
  { id: "content-license", label: "9. Your content" },
  { id: "certificates", label: "10. Certificates" },
  { id: "ai-tutor", label: "11. AI tutor & automated feedback" },
  { id: "ip", label: "12. Intellectual property" },
  { id: "termination", label: "13. Suspension & termination" },
  { id: "disclaimers", label: "14. Disclaimers & liability" },
  { id: "governing-law", label: "15. Governing law" },
  { id: "changes", label: "16. Changes to these terms" },
  { id: "contact", label: "17. Contact us" },
];

export default function TermsPage() {
  return (
    <LegalPage title="Terms of Service" lastUpdated="July 31, 2026" toc={TOC}>
      <LegalSection id="acceptance" title="1. Acceptance of terms">
        <p>
          These Terms of Service (&quot;Terms&quot;) govern your access to and use of SkillChain
          — the website, mobile experience, APIs, and related services (together, the
          &quot;Service&quot;) operated by MUIAA Ltd (&quot;SkillChain&quot;, &quot;we&quot;,
          &quot;us&quot;, or &quot;our&quot;), a company registered in Kenya. By creating an
          account, enrolling in a course, or otherwise using the Service, you agree to be bound by
          these Terms and our{" "}
          <Link href="/privacy" className="text-teal-400 hover:underline">
            Privacy Policy
          </Link>
          . If you do not agree, do not use the Service.
        </p>
      </LegalSection>

      <LegalSection id="service" title="2. Description of service">
        <p>
          SkillChain is a blockchain and AI education platform. Through the Service you can
          browse and enroll in courses, complete lessons, quizzes, graded assignments, and
          auto-graded coding exercises, join live instructor-led sessions over Zoom or Google
          Meet, participate in course discussions, receive an AI-assisted tutor and
          feedback-suggestion features, earn verifiable certificates on completion, and — for
          instructors and affiliates — author and monetize courses or refer new students.
        </p>
        <p>
          We may add, change, or remove features at any time. We&apos;ll try to give reasonable
          notice of changes that materially reduce the Service&apos;s functionality.
        </p>
      </LegalSection>

      <LegalSection id="accounts" title="3. Eligibility & accounts">
        <ul className="list-disc space-y-2 pl-5 marker:text-teal-400">
          <li>
            You must be at least 16 years old, or the age of digital consent in your
            jurisdiction, to create an account. If you are under 18, you confirm you have a
            parent or guardian&apos;s permission to use the Service.
          </li>
          <li>You must provide accurate registration information and keep it up to date.</li>
          <li>
            You are responsible for safeguarding your password and any multi-factor
            authentication device, and for all activity that happens under your account.
          </li>
          <li>One account per person. Do not share credentials or transfer your account.</li>
          <li>
            Notify us immediately at{" "}
            <a href="mailto:contact@skillchain.com" className="text-teal-400 hover:underline">
              contact@skillchain.com
            </a>{" "}
            if you suspect unauthorized use of your account.
          </li>
        </ul>
      </LegalSection>

      <LegalSection id="roles" title="4. Account roles">
        <p>
          The Service supports several account roles — student, instructor, affiliate,
          organization, and (internally) moderation, support, finance, and content-review roles
          for our team. Instructor and affiliate status is granted through an application or
          self-service enrollment step and can be revoked if these Terms are violated. Additional
          permissions attached to a role do not transfer if your account is suspended or
          terminated.
        </p>
      </LegalSection>

      <LegalSection id="instructors" title="5. Instructor terms">
        <ul className="list-disc space-y-2 pl-5 marker:text-teal-400">
          <li>
            You retain ownership of the courses, lessons, and materials you upload, and grant
            SkillChain a worldwide, non-exclusive license to host, reproduce, and display that
            content to deliver the Service to enrolled students.
          </li>
          <li>
            New and updated courses go through a review step before publication. We may reject or
            request changes to content that violates these Terms, infringes intellectual
            property, or is misleading.
          </li>
          <li>
            Earnings from paid enrollments accrue to your instructor wallet after applicable
            payment-processor fees and platform commission, and are paid out on request subject to
            our payout process and any minimum-balance threshold shown in your dashboard.
          </li>
          <li>
            You are responsible for the accuracy of any coupons or promotions you configure for
            your courses.
          </li>
          <li>
            Scheduling a live session connects your own Zoom or Google Meet account; you are
            responsible for conduct during sessions you host.
          </li>
        </ul>
      </LegalSection>

      <LegalSection id="payments" title="6. Payments, pricing & refunds">
        <p>
          Paid courses are billed in the currency and amount shown at checkout and processed
          through third-party payment providers, including Stripe, PayPal, Flutterwave,
          Paystack, and M-Pesa. SkillChain does not store your full card number or mobile-money
          PIN — that information is handled directly by the payment provider.
        </p>
        <p>
          Coupons and promotions are subject to the validity window, usage limits, and eligibility
          rules set by the instructor or SkillChain. Refunds are considered on a case-by-case
          basis and are not guaranteed once a course has been substantially completed, except
          where required by applicable consumer-protection law.
        </p>
      </LegalSection>

      <LegalSection id="live-sessions" title="7. Live sessions">
        <p>
          Live sessions are hosted on third-party conferencing platforms (Zoom or Google Meet).
          Registration is required, and the join link is only issued in the window immediately
          before a session starts. SkillChain is not responsible for outages, quality, or
          availability of the underlying conferencing provider. If a session is recorded, that
          recording may be made available to registered attendees after the session ends.
        </p>
      </LegalSection>

      <LegalSection id="conduct" title="8. Community guidelines">
        <p>You agree not to, on any part of the Service including course discussions and reviews:</p>
        <ul className="list-disc space-y-2 pl-5 marker:text-teal-400">
          <li>Post content that is unlawful, harassing, hateful, or sexually explicit.</li>
          <li>Infringe another person&apos;s intellectual property or privacy.</li>
          <li>
            Impersonate another person, misrepresent your affiliation, or submit work that is not
            your own for graded assignments or exercises.
          </li>
          <li>Upload malware or attempt to disrupt, reverse-engineer, or scrape the Service.</li>
          <li>Use the Service to sell or promote products unrelated to your course.</li>
        </ul>
        <p>
          We may remove content or suspend accounts that violate these guidelines, at our
          discretion.
        </p>
      </LegalSection>

      <LegalSection id="content-license" title="9. Your content">
        <p>
          &quot;Your content&quot; means anything you submit to the Service: discussion posts,
          reviews, assignment and coding-exercise submissions, profile information, and messages.
          You retain ownership of your content. By posting it, you grant SkillChain a
          non-exclusive, royalty-free license to store, display, and process it as needed to
          operate the Service — for example, showing your discussion post to other enrolled
          students, or passing an assignment submission to an instructor or our AI grading
          assistant for feedback.
        </p>
      </LegalSection>

      <LegalSection id="certificates" title="10. Certificates">
        <p>
          On completing a course&apos;s requirements, SkillChain issues a certificate with a
          unique, publicly verifiable identifier. Certificates confirm completion of SkillChain
          coursework; they are not a professional license, a university degree, or a guarantee of
          employment, and their recognition by any employer or institution is at that third
          party&apos;s discretion.
        </p>
      </LegalSection>

      <LegalSection id="ai-tutor" title="11. AI tutor & automated feedback">
        <p>
          AI-generated summaries, flashcards, tutoring responses, and AI-suggested grading
          feedback are provided to support your learning and are not professional, educational,
          financial, or legal advice. AI output can be incomplete or incorrect — verify anything
          important against course material or a human instructor before relying on it.
          AI-suggested grades on assignments are reviewed and can be adjusted by the instructor
          before they count.
        </p>
      </LegalSection>

      <LegalSection id="ip" title="12. Intellectual property">
        <p>
          SkillChain, its logo, and its associated trademarks and branding are the intellectual
          property of MUIAA Ltd. The platform&apos;s underlying software, design, and code are
          owned by MUIAA Ltd or its licensors. Except for the license you grant us to your own
          content under Section 9, and the license instructors grant under Section 5, nothing in
          these Terms transfers any intellectual property to you. Unauthorized reproduction,
          distribution, or modification of SkillChain&apos;s branding or platform code is
          prohibited.
        </p>
      </LegalSection>

      <LegalSection id="termination" title="13. Suspension & termination">
        <p>
          You may stop using the Service and close your account at any time. We may suspend or
          terminate your access if you violate these Terms, if required by law, or to protect the
          Service or other users. Where reasonably possible, we&apos;ll give notice first. Some
          provisions of these Terms — including intellectual property, disclaimers, and limitation
          of liability — survive termination.
        </p>
      </LegalSection>

      <LegalSection id="disclaimers" title="14. Disclaimers & limitation of liability">
        <p>
          The Service is provided &quot;as is&quot; without warranties of any kind, express or
          implied, including merchantability, fitness for a particular purpose, and
          non-infringement. We do not guarantee the Service will be uninterrupted, error-free, or
          that any course outcome (job placement, certification recognition, or income) will be
          achieved.
        </p>
        <p>
          To the maximum extent permitted by law, SkillChain and MUIAA Ltd are not liable for
          indirect, incidental, special, or consequential damages arising from your use of the
          Service. Nothing in these Terms limits liability that cannot be limited under applicable
          law.
        </p>
      </LegalSection>

      <LegalSection id="governing-law" title="15. Governing law">
        <p>
          These Terms are governed by the laws of the Republic of Kenya, without regard to
          conflict-of-law principles. Any dispute arising from these Terms or the Service will be
          subject to the exclusive jurisdiction of the courts of Kenya, unless applicable
          consumer-protection law in your country of residence gives you the right to bring a
          claim in your local courts.
        </p>
      </LegalSection>

      <LegalSection id="changes" title="16. Changes to these terms">
        <p>
          We may update these Terms from time to time. If a change is material, we&apos;ll notify
          you by email or an in-app notice before it takes effect. Continuing to use the Service
          after a change becomes effective means you accept the updated Terms.
        </p>
      </LegalSection>

      <LegalSection id="contact" title="17. Contact us">
        <p>Questions about these Terms can be sent to:</p>
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
