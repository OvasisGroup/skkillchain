// Central place for the values that feed page metadata, the sitemap,
// robots.txt, and JSON-LD — keeping the site's canonical URL and blurb in
// one spot so every entry point (layout, sitemap, structured data) agrees.

export const SITE_NAME = "SkillChain";

export const SITE_URL = (process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000").replace(
  /\/+$/,
  ""
);

export const SITE_DESCRIPTION =
  "SkillChain is a modern online learning platform: expert-led courses, live sessions, AI-powered tutoring, and verifiable certificates for blockchain and AI education in Africa.";

export const SITE_KEYWORDS = [
  "blockchain courses",
  "AI education",
  "online learning Africa",
  "SkillChain",
  "live coding sessions",
  "course certificates",
];

export function absoluteUrl(path: string): string {
  return `${SITE_URL}${path.startsWith("/") ? path : `/${path}`}`;
}

export function organizationJsonLd() {
  return {
    "@context": "https://schema.org",
    "@type": "Organization",
    name: SITE_NAME,
    url: SITE_URL,
    description: SITE_DESCRIPTION,
  };
}

export function websiteJsonLd() {
  return {
    "@context": "https://schema.org",
    "@type": "WebSite",
    name: SITE_NAME,
    url: SITE_URL,
    potentialAction: {
      "@type": "SearchAction",
      target: `${absoluteUrl("/courses")}?q={search_term_string}`,
      "query-input": "required name=search_term_string",
    },
  };
}
