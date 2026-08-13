"use client";

import { ChevronLeft, ChevronRight, ExternalLink, Images, Play, X } from "lucide-react";
import { useEffect, useState } from "react";
import type { HackathonGalleryImage } from "@/lib/api/types";
import { isDirectVideoFile, videoEmbedUrl } from "@/lib/video";

const THUMBNAIL_PREVIEW_COUNT = 6;

// Video thumbnails have no dedicated poster image field — a YouTube/Vimeo
// URL's own thumbnail isn't worth the extra round-trip/host-specific
// scraping for a preview grid, so video tiles get a plain dark tile with a
// play icon instead of trying to represent the video visually.
function GalleryTile({ item }: { item: HackathonGalleryImage }) {
  if (item.video_url) {
    return (
      <div className="flex h-full w-full items-center justify-center bg-emerald-950">
        <Play className="h-6 w-6 text-teal-300" fill="currentColor" />
      </div>
    );
  }
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={item.image ?? undefined}
      alt={item.caption || ""}
      className="h-full w-full object-cover transition-opacity group-hover:opacity-80"
    />
  );
}

function GalleryLightboxContent({ item }: { item: HackathonGalleryImage }) {
  const videoUrl = item.video_url;
  if (videoUrl) {
    const embedUrl = videoEmbedUrl(videoUrl);
    if (embedUrl) {
      return (
        <iframe
          src={embedUrl}
          title={item.caption || "Event video"}
          className="aspect-video max-h-[75vh] w-[min(90vw,1024px)] rounded-lg"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
        />
      );
    }
    if (isDirectVideoFile(videoUrl)) {
      return (
        <video
          src={videoUrl}
          controls
          className="max-h-[75vh] max-w-full rounded-lg"
        />
      );
    }
    return (
      <a
        href={videoUrl}
        target="_blank"
        rel="noreferrer noopener"
        className="flex items-center gap-2 rounded-full bg-teal-400 px-5 py-2.5 text-sm font-semibold text-emerald-950 hover:opacity-90"
      >
        Watch video <ExternalLink className="h-4 w-4" />
      </a>
    );
  }

  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={item.image ?? undefined}
      alt={item.caption || ""}
      className="max-h-[75vh] max-w-full rounded-lg object-contain"
    />
  );
}

export function HackathonGalleryViewer({ images }: { images: HackathonGalleryImage[] }) {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  useEffect(() => {
    if (openIndex === null) return;
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") setOpenIndex(null);
      if (e.key === "ArrowRight") setOpenIndex((i) => (i === null ? i : (i + 1) % images.length));
      if (e.key === "ArrowLeft") {
        setOpenIndex((i) => (i === null ? i : (i - 1 + images.length) % images.length));
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [openIndex, images.length]);

  if (images.length === 0) return null;

  const preview = images.slice(0, THUMBNAIL_PREVIEW_COUNT);
  const remaining = images.length - preview.length;

  return (
    <div>
      <h3 className="flex items-center gap-2 text-sm font-semibold text-foreground">
        <Images className="h-4 w-4 text-teal-400" />
        Gallery
      </h3>
      <div className="mt-3 grid grid-cols-3 gap-2 sm:grid-cols-6">
        {preview.map((item, index) => {
          const isLastPreview = index === preview.length - 1;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => setOpenIndex(index)}
              className="group relative aspect-square overflow-hidden rounded-lg border border-border bg-surface-hover"
            >
              <GalleryTile item={item} />
              {isLastPreview && remaining > 0 && (
                <span className="absolute inset-0 flex items-center justify-center bg-black/60 text-sm font-semibold text-white">
                  +{remaining}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {openIndex !== null && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-100 flex items-center justify-center bg-black/85 px-4"
          onClick={() => setOpenIndex(null)}
        >
          <button
            type="button"
            onClick={() => setOpenIndex(null)}
            aria-label="Close gallery"
            className="absolute right-4 top-4 rounded-full bg-white/10 p-2 text-white hover:bg-white/20"
          >
            <X className="h-5 w-5" />
          </button>

          {images.length > 1 && (
            <>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  setOpenIndex((i) => (i === null ? i : (i - 1 + images.length) % images.length));
                }}
                aria-label="Previous item"
                className="absolute left-4 top-1/2 -translate-y-1/2 rounded-full bg-white/10 p-2 text-white hover:bg-white/20"
              >
                <ChevronLeft className="h-6 w-6" />
              </button>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  setOpenIndex((i) => (i === null ? i : (i + 1) % images.length));
                }}
                aria-label="Next item"
                className="absolute right-4 top-1/2 -translate-y-1/2 rounded-full bg-white/10 p-2 text-white hover:bg-white/20"
              >
                <ChevronRight className="h-6 w-6" />
              </button>
            </>
          )}

          <div
            className="flex max-h-[85vh] max-w-4xl flex-col items-center"
            onClick={(e) => e.stopPropagation()}
          >
            <GalleryLightboxContent item={images[openIndex]} />
            {images[openIndex].caption && (
              <p className="mt-3 text-center text-sm text-white/70">{images[openIndex].caption}</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
