// Plain intent-URL <a> links, not the platforms' JS SDKs — no third-party
// script, no tracking pixel, and it works the same whether or not the
// visitor is logged into Twitter/LinkedIn in this browser.
function twitterShareUrl(url: string, title: string): string {
  const params = new URLSearchParams({ url, text: title });
  return `https://twitter.com/intent/tweet?${params.toString()}`;
}

function linkedInShareUrl(url: string): string {
  const params = new URLSearchParams({ url });
  return `https://www.linkedin.com/sharing/share-offsite/?${params.toString()}`;
}

function TwitterIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" {...props}>
      <path d="M18.9 2H22l-7.6 8.7L23.3 22h-7.1l-5.5-7.2L4.3 22H1.2l8.1-9.3L1 2h7.3l5 6.6L18.9 2Zm-1.2 18h1.9L7.4 4H5.4l12.3 16Z" />
    </svg>
  );
}

function LinkedInIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" {...props}>
      <path d="M20.45 20.45h-3.55v-5.57c0-1.33-.02-3.03-1.85-3.03-1.86 0-2.15 1.45-2.15 2.94v5.66H9.35V9h3.41v1.56h.05c.47-.9 1.63-1.85 3.36-1.85 3.6 0 4.26 2.37 4.26 5.45v6.29ZM5.34 7.43a2.06 2.06 0 1 1 0-4.12 2.06 2.06 0 0 1 0 4.12ZM7.12 20.45H3.56V9h3.56v11.45Z" />
    </svg>
  );
}

export function ShareButtons({ url, title }: { url: string; title: string }) {
  return (
    <div className="flex items-center gap-2" aria-label="Share this post">
      <span className="text-sm text-foreground/50">Share:</span>
      <a
        href={twitterShareUrl(url, title)}
        target="_blank"
        rel="noopener noreferrer"
        aria-label="Share on Twitter / X"
        className="flex h-9 w-9 items-center justify-center rounded-full border border-border text-foreground/60 transition-colors hover:border-teal-400/50 hover:text-teal-500 dark:hover:text-teal-300"
      >
        <TwitterIcon className="h-4 w-4" />
      </a>
      <a
        href={linkedInShareUrl(url)}
        target="_blank"
        rel="noopener noreferrer"
        aria-label="Share on LinkedIn"
        className="flex h-9 w-9 items-center justify-center rounded-full border border-border text-foreground/60 transition-colors hover:border-teal-400/50 hover:text-teal-500 dark:hover:text-teal-300"
      >
        <LinkedInIcon className="h-4 w-4" />
      </a>
    </div>
  );
}
