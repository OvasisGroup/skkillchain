"use client";

import { useState } from "react";
import { ApiError } from "@/lib/api/client";
import { uploadCourseCoverImage } from "@/lib/api/instructorCourses";

export function CourseCoverImage({
  courseId,
  coverImage,
  token,
  onUploaded,
}: {
  courseId: string;
  coverImage: string | null;
  token: string;
  onUploaded: (coverImage: string | null) => void;
}) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleFile(file: File | undefined) {
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const updated = await uploadCourseCoverImage(courseId, file, token);
      onUploaded(updated.cover_image);
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't upload the cover image.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="flex items-center gap-3">
      <div className="flex h-16 w-28 flex-none items-center justify-center overflow-hidden rounded-lg border border-border-strong bg-surface-hover">
        {coverImage ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={coverImage} alt="Course cover" className="h-full w-full object-cover" />
        ) : (
          <span className="text-xs text-foreground/30">No image</span>
        )}
      </div>
      <div>
        <label className="cursor-pointer rounded-full bg-teal-400/10 px-3 py-1.5 text-xs font-semibold text-teal-400 hover:bg-teal-400/20">
          {uploading ? "Uploading…" : coverImage ? "Change cover" : "Upload cover"}
          <input
            type="file"
            accept="image/*"
            disabled={uploading}
            onChange={(e) => handleFile(e.target.files?.[0])}
            className="hidden"
          />
        </label>
        {error && <p className="mt-1 text-xs text-rose-400">{error}</p>}
      </div>
    </div>
  );
}
