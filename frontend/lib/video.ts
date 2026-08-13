// Turns a YouTube/Vimeo watch/share URL into its embeddable iframe URL.
// Returns null for anything else (a direct video file URL, or a host we
// don't recognize) — callers fall back to a native <video> element or a
// plain link in that case, since not every video link is embeddable via
// iframe (a direct .mp4 link isn't, and never needs to be).
export function videoEmbedUrl(url: string): string | null {
  let parsed: URL;
  try {
    parsed = new URL(url);
  } catch {
    return null;
  }

  const host = parsed.hostname.replace(/^www\./, "");

  if (host === "youtube.com" || host === "m.youtube.com") {
    if (parsed.pathname === "/watch") {
      const id = parsed.searchParams.get("v");
      return id ? `https://www.youtube.com/embed/${id}` : null;
    }
    if (parsed.pathname.startsWith("/embed/")) {
      return `https://www.youtube.com${parsed.pathname}`;
    }
    if (parsed.pathname.startsWith("/shorts/")) {
      const id = parsed.pathname.split("/")[2];
      return id ? `https://www.youtube.com/embed/${id}` : null;
    }
    return null;
  }

  if (host === "youtu.be") {
    const id = parsed.pathname.slice(1);
    return id ? `https://www.youtube.com/embed/${id}` : null;
  }

  if (host === "vimeo.com") {
    const id = parsed.pathname.split("/").filter(Boolean)[0];
    return id && /^\d+$/.test(id) ? `https://player.vimeo.com/video/${id}` : null;
  }

  return null;
}

// A direct video file link (e.g. https://.../clip.mp4) is playable with a
// native <video> tag; anything else that isn't embeddable falls back to a
// plain "watch video" link instead.
const DIRECT_VIDEO_EXTENSIONS = [".mp4", ".webm", ".mov", ".m4v"];

export function isDirectVideoFile(url: string): boolean {
  try {
    const { pathname } = new URL(url);
    return DIRECT_VIDEO_EXTENSIONS.some((ext) => pathname.toLowerCase().endsWith(ext));
  } catch {
    return false;
  }
}
