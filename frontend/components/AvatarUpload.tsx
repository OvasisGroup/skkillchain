"use client";

import { useState } from "react";
import { ApiError } from "@/lib/api/client";
import { uploadAvatar } from "@/lib/api/auth";
import type { Me } from "@/lib/api/types";

export function AvatarUpload({
  avatar,
  accessToken,
  onUploaded,
}: {
  avatar: string | null;
  accessToken: string;
  onUploaded: (user: Me) => void;
}) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleFile(file: File | undefined) {
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const updated = await uploadAvatar(file, accessToken);
      onUploaded(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't upload the avatar.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="flex items-center gap-4">
      <div className="flex h-16 w-16 flex-none items-center justify-center overflow-hidden rounded-full border border-border-strong bg-surface-hover">
        {avatar ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={avatar} alt="Avatar" className="h-full w-full object-cover" />
        ) : (
          <span className="text-xs text-foreground/30">No photo</span>
        )}
      </div>
      <div>
        <label className="cursor-pointer rounded-full bg-teal-400/10 px-3 py-1.5 text-xs font-semibold text-teal-400 hover:bg-teal-400/20">
          {uploading ? "Uploading…" : avatar ? "Change photo" : "Upload photo"}
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
