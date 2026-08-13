// Central place for the values that feed page metadata, the sitemap,
// robots.txt, and JSON-LD — keeping the site's canonical URL and blurb in
// one spot so every entry point (layout, sitemap, structured data) agrees.

export const SITE_NAME = "SkillChain";

// `||`, not `??` — an unset Docker build-arg surfaces here as an empty
// string, not undefined (ENV NEXT_PUBLIC_SITE_URL=$NEXT_PUBLIC_SITE_URL
// still *sets* the var, just to ""), and `??` only falls back on
// null/undefined. `new URL(SITE_URL)` below and in app/layout.tsx would
// otherwise throw ERR_INVALID_URL on an empty string and fail the build.
export const SITE_URL = (process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000").replace(
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

// JSON.stringify does not escape `<`, `>`, U+2028 (LINE SEPARATOR), or
// U+2029 (PARAGRAPH SEPARATOR), so a user-controlled string (course/
// hackathon title, summary, etc.) containing `</script>` can break out of
// the JSON-LD <script> tag it's injected into via dangerouslySetInnerHTML
// and run arbitrary JS. Escaping those to \u-sequences keeps the JSON value
// identical while making it impossible to close the surrounding tag.
// U+2028/U+2029 are built via fromCharCode rather than written as literal
// source characters — embedded raw, they're parsed as line terminators by
// the TS/JS tokenizer itself and break the file.
const LINE_SEPARATOR = String.fromCharCode(0x2028);
const PARAGRAPH_SEPARATOR = String.fromCharCode(0x2029);

export function safeJsonLd(data: unknown): string {
  return JSON.stringify(data)
    .split("<")
    .join("\\u003c")
    .split(">")
    .join("\\u003e")
    .split(LINE_SEPARATOR)
    .join("\\u2028")
    .split(PARAGRAPH_SEPARATOR)
    .join("\\u2029");
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
