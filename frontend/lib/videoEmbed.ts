// Converts a YouTube/Vimeo watch URL into its embeddable iframe URL. Returns
// null for anything else (a direct media file URL, or an unrecognized page)
// so the caller falls back to a plain <video src> instead — a raw .mp4/.webm
// URL works fine in a <video> tag but not in an iframe, and vice versa for a
// YouTube page URL, which a <video> tag can't play at all.
export function toEmbeddableVideoUrl(url: string): string | null {
  let parsed: URL;
  try {
    parsed = new URL(url);
  } catch {
    return null;
  }
  const host = parsed.hostname.replace(/^www\.|^m\./, "");

  if (host === "youtube.com") {
    if (parsed.pathname === "/watch") {
      const id = parsed.searchParams.get("v");
      return id ? `https://www.youtube.com/embed/${id}` : null;
    }
    if (parsed.pathname.startsWith("/embed/")) return url;
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
    return id ? `https://player.vimeo.com/video/${id}` : null;
  }
  return null;
}
