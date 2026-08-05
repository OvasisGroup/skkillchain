"use client";

import { useState } from "react";
import { AvatarUpload } from "@/components/AvatarUpload";
import { LoadingState } from "@/components/dashboard/DashboardStates";
import { ApiError } from "@/lib/api/client";
import { updateMe } from "@/lib/api/auth";
import type { Me } from "@/lib/api/types";
import { useAuth } from "@/lib/auth/AuthContext";
import { Reveal } from "@/components/animation/Reveal";

export default function ProfilePage() {
  const { user, accessToken, setUser } = useAuth();

  if (!user || !accessToken) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-16">
        <LoadingState label="Loading your profile…" />
      </div>
    );
  }

  return (
    <ProfileForm user={user} accessToken={accessToken} onSaved={setUser} />
  );
}

function ProfileForm({
  user,
  accessToken,
  onSaved,
}: {
  user: Me;
  accessToken: string;
  onSaved: (user: Me) => void;
}) {
  const [email, setEmail] = useState(user.email);
  const [firstName, setFirstName] = useState(user.profile.first_name);
  const [lastName, setLastName] = useState(user.profile.last_name);
  const [bio, setBio] = useState(user.profile.bio);
  const [locale, setLocale] = useState(user.profile.locale);
  const [timezone, setTimezone] = useState(user.profile.timezone);
  const [linkedinUrl, setLinkedinUrl] = useState(user.profile.linkedin_url);
  const [twitterUrl, setTwitterUrl] = useState(user.profile.twitter_url);
  const [githubUrl, setGithubUrl] = useState(user.profile.github_url);
  const [youtubeUrl, setYoutubeUrl] = useState(user.profile.youtube_url);
  const [websiteUrl, setWebsiteUrl] = useState(user.profile.website_url);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      const updated = await updateMe(
        {
          email,
          profile: {
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
        },
        accessToken
      );
      onSaved(updated);
      setSaved(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't save your profile.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Reveal className="mx-auto max-w-3xl px-6 py-16">
      <div>
        <p className="text-sm font-semibold uppercase tracking-wider text-lime-400">Account</p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          Profile
        </h1>
        <p className="mt-3 text-lg text-foreground/60">{user.email}</p>
      </div>

      {user.roles.length > 0 && (
        <div className="mt-6 flex flex-wrap gap-2">
          {user.roles.map((role) => (
            <span
              key={role}
              className="rounded-full bg-teal-400/10 px-2.5 py-0.5 text-xs font-medium capitalize text-teal-400"
            >
              {role.replace(/_/g, " ")}
            </span>
          ))}
        </div>
      )}

      <div className="mt-10 rounded-2xl border border-border bg-surface p-6">
        <span className="text-sm font-medium text-foreground/80">Profile photo</span>
        <div className="mt-2">
          <AvatarUpload avatar={user.profile.avatar} accessToken={accessToken} onUploaded={onSaved} />
        </div>
      </div>

      <form onSubmit={handleSubmit} className="mt-6 space-y-5 rounded-2xl border border-border bg-surface p-6">
        <label className="block">
          <span className="text-sm font-medium text-foreground/80">Email address</span>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mt-1.5 w-full rounded-lg border border-border-strong bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-teal-400"
          />
        </label>

        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
          <label className="block">
            <span className="text-sm font-medium text-foreground/80">First name</span>
            <input
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              className="mt-1.5 w-full rounded-lg border border-border-strong bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-teal-400"
            />
          </label>
          <label className="block">
            <span className="text-sm font-medium text-foreground/80">Last name</span>
            <input
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              className="mt-1.5 w-full rounded-lg border border-border-strong bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-teal-400"
            />
          </label>
        </div>

        <label className="block">
          <span className="text-sm font-medium text-foreground/80">Bio</span>
          <textarea
            value={bio}
            onChange={(e) => setBio(e.target.value)}
            rows={4}
            placeholder="A short introduction other users will see on your public profile."
            className="mt-1.5 w-full rounded-lg border border-border-strong bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-teal-400"
          />
        </label>

        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
          <label className="block">
            <span className="text-sm font-medium text-foreground/80">Locale</span>
            <input
              value={locale}
              onChange={(e) => setLocale(e.target.value)}
              placeholder="en"
              className="mt-1.5 w-full rounded-lg border border-border-strong bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-teal-400"
            />
          </label>
          <label className="block">
            <span className="text-sm font-medium text-foreground/80">Timezone</span>
            <input
              value={timezone}
              onChange={(e) => setTimezone(e.target.value)}
              placeholder="UTC"
              className="mt-1.5 w-full rounded-lg border border-border-strong bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-teal-400"
            />
          </label>
        </div>

        <div>
          <span className="text-sm font-medium text-foreground/80">Social contacts (optional)</span>
          <div className="mt-2 grid grid-cols-1 gap-5 sm:grid-cols-2">
            <label className="block">
              <span className="text-xs text-foreground/60">LinkedIn</span>
              <input
                type="url"
                value={linkedinUrl}
                onChange={(e) => setLinkedinUrl(e.target.value)}
                placeholder="https://linkedin.com/in/username"
                className="mt-1.5 w-full rounded-lg border border-border-strong bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-teal-400"
              />
            </label>
            <label className="block">
              <span className="text-xs text-foreground/60">Twitter / X</span>
              <input
                type="url"
                value={twitterUrl}
                onChange={(e) => setTwitterUrl(e.target.value)}
                placeholder="https://twitter.com/username"
                className="mt-1.5 w-full rounded-lg border border-border-strong bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-teal-400"
              />
            </label>
            <label className="block">
              <span className="text-xs text-foreground/60">GitHub</span>
              <input
                type="url"
                value={githubUrl}
                onChange={(e) => setGithubUrl(e.target.value)}
                placeholder="https://github.com/username"
                className="mt-1.5 w-full rounded-lg border border-border-strong bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-teal-400"
              />
            </label>
            <label className="block">
              <span className="text-xs text-foreground/60">YouTube</span>
              <input
                type="url"
                value={youtubeUrl}
                onChange={(e) => setYoutubeUrl(e.target.value)}
                placeholder="https://youtube.com/@channel"
                className="mt-1.5 w-full rounded-lg border border-border-strong bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-teal-400"
              />
            </label>
            <label className="block">
              <span className="text-xs text-foreground/60">Website</span>
              <input
                type="url"
                value={websiteUrl}
                onChange={(e) => setWebsiteUrl(e.target.value)}
                placeholder="https://example.com"
                className="mt-1.5 w-full rounded-lg border border-border-strong bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-teal-400"
              />
            </label>
          </div>
        </div>

        {error && <p className="text-sm text-rose-400">{error}</p>}
        {saved && !error && <p className="text-sm text-emerald-400">Profile saved.</p>}

        <button
          type="submit"
          disabled={saving}
          className="rounded-full bg-teal-400 px-6 py-2.5 text-sm font-semibold text-emerald-950 transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {saving ? "Saving…" : "Save changes"}
        </button>
      </form>
    </Reveal>
  );
}
