import Link from "next/link";
import { Logo } from "./Logo";

const COLUMNS: { title: string; links: { label: string; href: string }[] }[] = [
  {
    title: "Platform",
    links: [
      { label: "Browse courses", href: "/courses" },
      { label: "For instructors", href: "/instructors" },
      { label: "Live sessions", href: "/live-sessions" },
    ],
  },
  {
    title: "Company",
    links: [{ label: "About", href: "/about" }],
  },
  {
    title: "Support",
    links: [
      { label: "Help center", href: "/help" },
      { label: "Contact us", href: "/contact" },
    ],
  },
  {
    title: "Legal",
    links: [
      { label: "Privacy", href: "/privacy" },
      { label: "Terms", href: "/terms" },
    ],
  },
];

export function Footer() {
  return (
    <footer className="border-t border-border bg-background">
      <div className="mx-auto max-w-7xl px-6 py-14">
        <div className="grid grid-cols-2 gap-10 sm:grid-cols-3 md:grid-cols-5">
          <div className="col-span-2 sm:col-span-3 md:col-span-1">
            <Logo />
            <p className="mt-4 max-w-xs text-sm text-foreground/50">
              Learn new skills, earn verifiable certificates, and build a career with courses
              taught by working practitioners.
            </p>
          </div>
          {COLUMNS.map((column) => (
            <div key={column.title}>
              <h3 className="text-sm font-semibold text-foreground">
                {column.title}
              </h3>
              <ul className="mt-4 space-y-3">
                {column.links.map((link) => (
                  <li key={link.label}>
                    <Link
                      href={link.href}
                      className="text-sm text-foreground/50 transition-colors hover:text-teal-300"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="mt-12 flex flex-col items-center justify-between gap-4 border-t border-border pt-8 text-sm text-foreground/40 sm:flex-row">
          <p>&copy; {new Date().getFullYear()} SkillChain. All rights reserved.</p>
        </div>
        <p className="mt-6 text-xs leading-relaxed text-foreground/35">
          Skillchain and its associated trademarks, branding, and digital assets are the
          intellectual property of MUUIA Ltd. Unauthorized reproduction, distribution, or
          modification of any content, including but not limited to text, graphics, logos,
          platform code, and user-generated content, is strictly prohibited. SkillChain is a
          community-driven skill-sharing platform designed to connect learners and educators. It
          does not constitute professional, educational, or financial advice. Users are
          responsible for ensuring compliance with applicable regulations, including data
          protection laws and any relevant guidelines issued by regulatory authorities in their
          jurisdiction.
        </p>
      </div>
    </footer>
  );
}
