"use client";

import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { ArrowLeft } from "lucide-react";
import { authInputClass, authLabelClass } from "@/components/AuthCard";
import { AdminAvatarUpload } from "@/components/dashboard/AdminAvatarUpload";
import { ErrorState, LoadingState } from "@/components/dashboard/DashboardStates";
import { Panel } from "@/components/dashboard/Panel";
import { getAdminUserProfile, updateAdminUserProfile } from "@/lib/api/admin";
import { ApiError } from "@/lib/api/client";
import type { Profile } from "@/lib/api/types";
import { useAuth } from "@/lib/auth/AuthContext";

export default function AdminInstructorEditPage() {
  const { id } = useParams<{ id: string }>();
  const email = useSearchParams().get("email");
  const router = useRouter();
  const { accessToken } = useAuth();

  const [profile, setProfile] = useState<Profile | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [bio, setBio] = useState("");
  const [locale, setLocale] = useState("");
  const [timezone, setTimezone] = useState("");
  const [linkedinUrl, setLinkedinUrl] = useState("");
  const [twitterUrl, setTwitterUrl] = useState("");
  const [githubUrl, setGithubUrl] = useState("");
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [websiteUrl, setWebsiteUrl] = useState("");

  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!accessToken) return;
    let cancelled = false;
    getAdminUserProfile(id, accessToken)
      .then((data) => {
        if (cancelled) return;
        setProfile(data);
        setFirstName(data.first_name);
        setLastName(data.last_name);
        setBio(data.bio);
        setLocale(data.locale);
        setTimezone(data.timezone);
        setLinkedinUrl(data.linkedin_url);
        setTwitterUrl(data.twitter_url);
        setGithubUrl(data.github_url);
        setYoutubeUrl(data.youtube_url);
        setWebsiteUrl(data.website_url);
      })
      .catch((err) => {
        if (!cancelled) {
          setLoadError(err instanceof ApiError ? err.message_ : "Couldn't load this instructor.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [id, accessToken]);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!accessToken) return;
    setSaving(true);
    setSaveError(null);
    setSaved(false);
    try {
      const updated = await updateAdminUserProfile(
        id,
        {
          first_name: firstName,
          last_name: lastName,
          bio,
          locale,
          timezone,
          linkedin_url: linkedinUrl,
          twitter_url: twitterUrl,
          github_url: githubUrl,
          youtube_url: youtubeUrl,
          website_url: websiteUrl,
        },
        accessToken
      );
      setProfile(updated);
      setSaved(true);
    } catch (err) {
      setSaveError(err instanceof ApiError ? err.message_ : "Couldn't save this instructor.");
    } finally {
      setSaving(false);
    }
  }

  if (loadError && !profile) return <ErrorState message={loadError} />;
  if (!profile || !accessToken) return <LoadingState label="Loading instructor…" />;

  return (
    <div className="mx-auto max-w-2xl space-y-8">
      <div>
        <button
          type="button"
          onClick={() => router.push("/dashboard/instructors")}
          className="flex items-center gap-1.5 text-sm text-foreground/50 hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" /> Back to instructors
        </button>
        <h1 className="mt-4 text-2xl font-semibold text-foreground">
          {[firstName, lastName].filter(Boolean).join(" ") || "Instructor"}
        </h1>
        {email && <p className="mt-1 text-sm text-foreground/50">{email}</p>}
      </div>

      <Panel title="Profile photo">
        <AdminAvatarUpload
          userId={id}
          avatar={profile.avatar}
          accessToken={accessToken}
          onUploaded={(avatar) => setProfile((prev) => (prev ? { ...prev, avatar } : prev))}
        />
      </Panel>

      <Panel title="Details" subtitle="Editable on the instructor's behalf.">
        <form onSubmit={handleSubmit} className="space-y-5">
          {saveError && <div className="rounded-lg bg-red-500/10 p-3 text-sm text-red-400">{saveError}</div>}
          {saved && !saveError && <p className="text-sm text-emerald-400">Saved.</p>}

          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
            <div>
              <label htmlFor="first-name" className={authLabelClass}>
                First name
              </label>
              <input
                id="first-name"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                className={authInputClass}
              />
            </div>
            <div>
              <label htmlFor="last-name" className={authLabelClass}>
                Last name
              </label>
              <input
                id="last-name"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                className={authInputClass}
              />
            </div>
          </div>

          <div>
            <label htmlFor="bio" className={authLabelClass}>
              Bio
            </label>
            <textarea
              id="bio"
              rows={4}
              value={bio}
              onChange={(e) => setBio(e.target.value)}
              placeholder="A short introduction shown on this instructor's public profile."
              className={authInputClass}
            />
          </div>

          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
            <div>
              <label htmlFor="locale" className={authLabelClass}>
                Locale
              </label>
              <input
                id="locale"
                value={locale}
                onChange={(e) => setLocale(e.target.value)}
                placeholder="en"
                className={authInputClass}
              />
            </div>
            <div>
              <label htmlFor="timezone" className={authLabelClass}>
                Timezone
              </label>
              <input
                id="timezone"
                value={timezone}
                onChange={(e) => setTimezone(e.target.value)}
                placeholder="UTC"
                className={authInputClass}
              />
            </div>
          </div>

          <div>
            <span className={authLabelClass}>Social contacts (optional)</span>
            <div className="mt-2 grid grid-cols-1 gap-5 sm:grid-cols-2">
              <div>
                <span className="text-xs text-foreground/60">LinkedIn</span>
                <input
                  type="url"
                  value={linkedinUrl}
                  onChange={(e) => setLinkedinUrl(e.target.value)}
                  placeholder="https://linkedin.com/in/username"
                  className={authInputClass}
                />
              </div>
              <div>
                <span className="text-xs text-foreground/60">Twitter / X</span>
                <input
                  type="url"
                  value={twitterUrl}
                  onChange={(e) => setTwitterUrl(e.target.value)}
                  placeholder="https://twitter.com/username"
                  className={authInputClass}
                />
              </div>
              <div>
                <span className="text-xs text-foreground/60">GitHub</span>
                <input
                  type="url"
                  value={githubUrl}
                  onChange={(e) => setGithubUrl(e.target.value)}
                  placeholder="https://github.com/username"
                  className={authInputClass}
                />
              </div>
              <div>
                <span className="text-xs text-foreground/60">YouTube</span>
                <input
                  type="url"
                  value={youtubeUrl}
                  onChange={(e) => setYoutubeUrl(e.target.value)}
                  placeholder="https://youtube.com/@channel"
                  className={authInputClass}
                />
              </div>
              <div>
                <span className="text-xs text-foreground/60">Website</span>
                <input
                  type="url"
                  value={websiteUrl}
                  onChange={(e) => setWebsiteUrl(e.target.value)}
                  placeholder="https://example.com"
                  className={authInputClass}
                />
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={saving}
            className="rounded-full bg-teal-400 px-6 py-2.5 text-sm font-semibold text-emerald-950 transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {saving ? "Saving…" : "Save changes"}
          </button>
        </form>
      </Panel>
    </div>
  );
}
