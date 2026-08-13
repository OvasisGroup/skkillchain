"use client";

import { ArrowLeft, ImagePlus, Play, Trash2, Trophy, Video } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { authInputClass, authLabelClass } from "@/components/AuthCard";
import { DataTable } from "@/components/dashboard/DataTable";
import { ErrorState, LoadingState } from "@/components/dashboard/DashboardStates";
import { Panel } from "@/components/dashboard/Panel";
import {
  addAdminHackathonGalleryVideo,
  cancelAdminHackathon,
  declareAdminHackathonWinner,
  deleteAdminHackathonGalleryImage,
  getAdminHackathon,
  listAdminHackathonGalleryImages,
  listAdminHackathonRegistrations,
  updateAdminHackathon,
  uploadAdminHackathonGalleryImage,
} from "@/lib/api/adminHackathons";
import { ApiError } from "@/lib/api/client";
import type {
  HackathonGalleryImage,
  HackathonOrganizerRegistration,
  HackathonWriteResult,
} from "@/lib/api/types";
import { useAuth } from "@/lib/auth/AuthContext";

const STATUS_STYLES: Record<string, string> = {
  draft: "bg-foreground/10 text-foreground/70",
  published: "bg-emerald-500/10 text-emerald-400",
  canceled: "bg-rose-500/10 text-rose-400",
};

// HackathonWriteResult's dates are full ISO strings; <input type="datetime-local">
// needs "YYYY-MM-DDTHH:mm" with no timezone/seconds — this trims to that.
function toDateTimeLocal(iso: string | null): string {
  if (!iso) return "";
  return new Date(iso).toISOString().slice(0, 16);
}

export default function AdminManageHackathonPage() {
  const { id } = useParams<{ id: string }>();
  const { accessToken } = useAuth();

  const [hackathon, setHackathon] = useState<HackathonWriteResult | null>(null);
  const [registrations, setRegistrations] = useState<HackathonOrganizerRegistration[] | null>(null);
  const [galleryImages, setGalleryImages] = useState<HackathonGalleryImage[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [winnerBusyId, setWinnerBusyId] = useState<string | null>(null);
  const [placements, setPlacements] = useState<Record<string, string>>({});
  const [prizes, setPrizes] = useState<Record<string, string>>({});

  // Edit form state
  const [summary, setSummary] = useState("");
  const [description, setDescription] = useState("");
  const [requirements, setRequirements] = useState("");
  const [prizeSummary, setPrizeSummary] = useState("");
  const [registrationDeadline, setRegistrationDeadline] = useState("");
  const [submissionDeadline, setSubmissionDeadline] = useState("");
  const [startsAt, setStartsAt] = useState("");
  const [endsAt, setEndsAt] = useState("");
  const [capacity, setCapacity] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  // Gallery upload state
  const [uploadCaption, setUploadCaption] = useState("");
  const [uploading, setUploading] = useState(false);
  const [deletingImageId, setDeletingImageId] = useState<string | null>(null);
  const [videoUrlInput, setVideoUrlInput] = useState("");
  const [videoCaption, setVideoCaption] = useState("");
  const [addingVideo, setAddingVideo] = useState(false);

  useEffect(() => {
    if (!accessToken || !id) return;
    let cancelled = false;

    async function load() {
      const token = accessToken as string;
      const [detail, registrationsPage, galleryPage] = await Promise.all([
        getAdminHackathon(id, token),
        listAdminHackathonRegistrations(id, token),
        listAdminHackathonGalleryImages(id, token),
      ]);
      if (cancelled) return;
      setHackathon(detail);
      setRegistrations(registrationsPage.results);
      setGalleryImages(galleryPage.results);
      setSummary(detail.summary);
      setDescription(detail.description);
      setRequirements(detail.requirements);
      setPrizeSummary(detail.prize_summary);
      setRegistrationDeadline(toDateTimeLocal(detail.registration_deadline));
      setSubmissionDeadline(toDateTimeLocal(detail.submission_deadline));
      setStartsAt(toDateTimeLocal(detail.starts_at));
      setEndsAt(toDateTimeLocal(detail.ends_at));
      setCapacity(detail.capacity !== null ? String(detail.capacity) : "");
    }

    load().catch((err) => {
      if (cancelled) return;
      setError(err instanceof ApiError ? err.message_ : "Couldn't load this hackathon.");
    });

    return () => {
      cancelled = true;
    };
  }, [accessToken, id]);

  async function handleSaveDetails(event: React.FormEvent) {
    event.preventDefault();
    if (!accessToken || !hackathon) return;
    setSaving(true);
    setSaved(false);
    setError(null);
    try {
      const updated = await updateAdminHackathon(
        hackathon.id,
        {
          summary,
          description,
          requirements,
          prize_summary: prizeSummary,
          registration_deadline: new Date(registrationDeadline).toISOString(),
          submission_deadline: new Date(submissionDeadline).toISOString(),
          starts_at: new Date(startsAt).toISOString(),
          ends_at: new Date(endsAt).toISOString(),
          capacity: capacity ? Number(capacity) : null,
        },
        accessToken
      );
      setHackathon(updated);
      setSaved(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't save these changes.");
    } finally {
      setSaving(false);
    }
  }

  async function handleCancel() {
    if (!accessToken || !hackathon) return;
    setBusy(true);
    try {
      const updated = await cancelAdminHackathon(hackathon.id, accessToken);
      setHackathon((prev) => (prev ? { ...prev, status: updated.status } : prev));
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't cancel this hackathon.");
    } finally {
      setBusy(false);
    }
  }

  async function handleDeclareWinner(registrationId: string) {
    if (!accessToken || !hackathon) return;
    const placement = Number(placements[registrationId] ?? "1");
    setWinnerBusyId(registrationId);
    setError(null);
    try {
      await declareAdminHackathonWinner(
        hackathon.id,
        { registration_id: registrationId, placement, prize_description: prizes[registrationId] },
        accessToken
      );
      const registrationsPage = await listAdminHackathonRegistrations(hackathon.id, accessToken);
      setRegistrations(registrationsPage.results);
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't declare this winner.");
    } finally {
      setWinnerBusyId(null);
    }
  }

  async function handleUploadImage(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file || !accessToken || !hackathon) return;
    setUploading(true);
    setError(null);
    try {
      const image = await uploadAdminHackathonGalleryImage(
        hackathon.id,
        file,
        uploadCaption,
        accessToken
      );
      setGalleryImages((prev) => (prev ? [...prev, image] : [image]));
      setUploadCaption("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't upload this image.");
    } finally {
      setUploading(false);
    }
  }

  async function handleAddVideo() {
    if (!videoUrlInput || !accessToken || !hackathon) return;
    setAddingVideo(true);
    setError(null);
    try {
      const video = await addAdminHackathonGalleryVideo(
        hackathon.id,
        videoUrlInput,
        videoCaption,
        accessToken
      );
      setGalleryImages((prev) => (prev ? [...prev, video] : [video]));
      setVideoUrlInput("");
      setVideoCaption("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't add this video.");
    } finally {
      setAddingVideo(false);
    }
  }

  async function handleDeleteImage(imageId: string) {
    if (!accessToken || !hackathon) return;
    setDeletingImageId(imageId);
    setError(null);
    try {
      await deleteAdminHackathonGalleryImage(hackathon.id, imageId, accessToken);
      setGalleryImages((prev) => prev?.filter((img) => img.id !== imageId) ?? prev);
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't delete this image.");
    } finally {
      setDeletingImageId(null);
    }
  }

  if (error && !hackathon) return <ErrorState message={error} />;
  if (!hackathon || !registrations || !galleryImages) {
    return <LoadingState label="Loading hackathon…" />;
  }

  return (
    <div className="space-y-8">
      <div>
        <Link
          href="/dashboard/admin"
          className="flex items-center gap-1.5 text-sm text-foreground/50 hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" /> Back to admin
        </Link>
        <div className="mt-3 flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-semibold text-foreground sm:text-3xl">
                {hackathon.title}
              </h1>
              <span
                className={`rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${STATUS_STYLES[hackathon.status] ?? ""}`}
              >
                {hackathon.status}
              </span>
            </div>
            <p className="mt-1 text-sm text-foreground/50">
              {hackathon.host_type === "partner"
                ? `In partnership with ${hackathon.partner_name || "a partner organization"}`
                : "Hosted internally"}
            </p>
          </div>
          <div className="flex gap-2">
            {hackathon.status !== "canceled" && (
              <button
                type="button"
                onClick={handleCancel}
                disabled={busy}
                className="rounded-full border border-border-strong px-4 py-1.5 text-sm font-semibold text-foreground/80 transition-colors hover:bg-surface-hover disabled:opacity-50"
              >
                Force-cancel
              </button>
            )}
            <Link
              href={`/hackathons/${hackathon.id}`}
              className="rounded-full border border-border-strong px-4 py-1.5 text-sm font-semibold text-foreground/80 transition-colors hover:bg-surface-hover"
            >
              View public page
            </Link>
          </div>
        </div>
      </div>

      {error && <div className="rounded-lg bg-red-500/10 p-3 text-sm text-red-400">{error}</div>}

      <Panel title="Edit details">
        <form onSubmit={handleSaveDetails} className="space-y-5">
          <div>
            <label htmlFor="summary" className={authLabelClass}>
              Short summary
            </label>
            <input
              id="summary"
              type="text"
              value={summary}
              onChange={(e) => setSummary(e.target.value)}
              className={authInputClass}
            />
          </div>
          <div>
            <label htmlFor="description" className={authLabelClass}>
              Description
            </label>
            <textarea
              id="description"
              rows={4}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className={authInputClass}
            />
          </div>
          <div>
            <label htmlFor="requirements" className={authLabelClass}>
              Requirements
            </label>
            <textarea
              id="requirements"
              rows={3}
              value={requirements}
              onChange={(e) => setRequirements(e.target.value)}
              className={authInputClass}
            />
          </div>
          <div>
            <label htmlFor="prizeSummary" className={authLabelClass}>
              Prize summary
            </label>
            <input
              id="prizeSummary"
              type="text"
              value={prizeSummary}
              onChange={(e) => setPrizeSummary(e.target.value)}
              className={authInputClass}
              placeholder="$10,000 in prizes"
            />
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label htmlFor="registrationDeadline" className={authLabelClass}>
                Registration deadline
              </label>
              <input
                id="registrationDeadline"
                type="datetime-local"
                required
                value={registrationDeadline}
                onChange={(e) => setRegistrationDeadline(e.target.value)}
                className={authInputClass}
              />
            </div>
            <div>
              <label htmlFor="submissionDeadline" className={authLabelClass}>
                Submission deadline
              </label>
              <input
                id="submissionDeadline"
                type="datetime-local"
                required
                value={submissionDeadline}
                onChange={(e) => setSubmissionDeadline(e.target.value)}
                className={authInputClass}
              />
            </div>
            <div>
              <label htmlFor="startsAt" className={authLabelClass}>
                Starts
              </label>
              <input
                id="startsAt"
                type="datetime-local"
                required
                value={startsAt}
                onChange={(e) => setStartsAt(e.target.value)}
                className={authInputClass}
              />
            </div>
            <div>
              <label htmlFor="endsAt" className={authLabelClass}>
                Ends
              </label>
              <input
                id="endsAt"
                type="datetime-local"
                required
                value={endsAt}
                onChange={(e) => setEndsAt(e.target.value)}
                className={authInputClass}
              />
            </div>
          </div>
          <div>
            <label htmlFor="capacity" className={authLabelClass}>
              Capacity (optional)
            </label>
            <input
              id="capacity"
              type="number"
              min={1}
              value={capacity}
              onChange={(e) => setCapacity(e.target.value)}
              className={authInputClass}
              placeholder="Leave blank for unlimited"
            />
          </div>
          <div className="flex items-center gap-3">
            <button
              type="submit"
              disabled={saving}
              className="rounded-full bg-teal-400 px-5 py-2.5 text-sm font-semibold text-emerald-950 transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {saving ? "Saving…" : "Save changes"}
            </button>
            {saved && <span className="text-sm text-emerald-400">Saved.</span>}
          </div>
        </form>
      </Panel>

      <Panel title="Registrations & submissions">
        <DataTable
          rows={registrations}
          getRowKey={(r) => r.id}
          emptyMessage="No one has registered yet."
          columns={[
            { header: "Participant", cell: (r) => r.participant.email },
            { header: "Team", cell: (r) => r.team_name || "—" },
            {
              header: "Status",
              cell: (r) => <span className="capitalize">{r.status}</span>,
            },
            {
              header: "Submission",
              cell: (r) =>
                r.submission ? (
                  <a
                    href={r.submission.repo_url || r.submission.demo_url || undefined}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-teal-400 hover:underline"
                  >
                    {r.submission.title}
                  </a>
                ) : (
                  <span className="text-foreground/40">Not submitted</span>
                ),
            },
            {
              header: "Declare winner",
              cell: (r) =>
                r.submission ? (
                  <div className="flex flex-wrap items-center gap-1.5">
                    <input
                      type="number"
                      min={1}
                      placeholder="#"
                      value={placements[r.id] ?? ""}
                      onChange={(e) =>
                        setPlacements((prev) => ({ ...prev, [r.id]: e.target.value }))
                      }
                      className="w-14 rounded-lg border border-border-strong bg-surface px-2 py-1 text-xs"
                    />
                    <input
                      type="text"
                      placeholder="Prize"
                      value={prizes[r.id] ?? ""}
                      onChange={(e) => setPrizes((prev) => ({ ...prev, [r.id]: e.target.value }))}
                      className="w-28 rounded-lg border border-border-strong bg-surface px-2 py-1 text-xs"
                    />
                    <button
                      type="button"
                      onClick={() => handleDeclareWinner(r.id)}
                      disabled={winnerBusyId === r.id}
                      className="flex items-center gap-1 rounded-full bg-teal-400 px-3 py-1 text-xs font-semibold text-emerald-950 transition-opacity hover:opacity-90 disabled:opacity-50"
                    >
                      <Trophy className="h-3.5 w-3.5" />
                      {winnerBusyId === r.id ? "Saving…" : "Award"}
                    </button>
                  </div>
                ) : (
                  <span className="text-foreground/30">—</span>
                ),
            },
          ]}
        />
      </Panel>

      <Panel title="Gallery">
        <div className="flex flex-wrap items-end gap-2">
          <div>
            <label htmlFor="caption" className={authLabelClass}>
              Caption (optional)
            </label>
            <input
              id="caption"
              type="text"
              value={uploadCaption}
              onChange={(e) => setUploadCaption(e.target.value)}
              className={`${authInputClass} w-56`}
              placeholder="Demo day, closing ceremony…"
            />
          </div>
          <label
            className={`flex cursor-pointer items-center gap-2 rounded-full bg-teal-400 px-4 py-2.5 text-sm font-semibold text-emerald-950 transition-opacity hover:opacity-90 ${
              uploading ? "pointer-events-none opacity-50" : ""
            }`}
          >
            <ImagePlus className="h-4 w-4" />
            {uploading ? "Uploading…" : "Upload image"}
            <input
              type="file"
              accept="image/*"
              onChange={handleUploadImage}
              disabled={uploading}
              className="hidden"
            />
          </label>
        </div>

        <div className="mt-3 flex flex-wrap items-end gap-2">
          <div>
            <label htmlFor="video-caption" className={authLabelClass}>
              Video caption (optional)
            </label>
            <input
              id="video-caption"
              type="text"
              value={videoCaption}
              onChange={(e) => setVideoCaption(e.target.value)}
              className={`${authInputClass} w-56`}
              placeholder="Recap, keynote…"
            />
          </div>
          <div>
            <label htmlFor="video-url" className={authLabelClass}>
              Video URL
            </label>
            <input
              id="video-url"
              type="url"
              value={videoUrlInput}
              onChange={(e) => setVideoUrlInput(e.target.value)}
              className={`${authInputClass} w-72`}
              placeholder="https://youtube.com/watch?v=…"
            />
          </div>
          <button
            type="button"
            onClick={handleAddVideo}
            disabled={addingVideo || !videoUrlInput}
            className="flex items-center gap-2 rounded-full bg-teal-400 px-4 py-2.5 text-sm font-semibold text-emerald-950 transition-opacity hover:opacity-90 disabled:pointer-events-none disabled:opacity-50"
          >
            <Video className="h-4 w-4" />
            {addingVideo ? "Adding…" : "Add video"}
          </button>
        </div>

        {galleryImages.length === 0 ? (
          <p className="mt-4 text-sm text-foreground/50">No gallery items yet.</p>
        ) : (
          <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-6">
            {galleryImages.map((item) => (
              <div key={item.id} className="group relative aspect-square overflow-hidden rounded-lg border border-border">
                {item.video_url ? (
                  <div className="flex h-full w-full items-center justify-center bg-emerald-950">
                    <Play className="h-6 w-6 text-teal-300" fill="currentColor" />
                  </div>
                ) : (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={item.image ?? undefined}
                    alt={item.caption || ""}
                    className="h-full w-full object-cover"
                  />
                )}
                <button
                  type="button"
                  onClick={() => handleDeleteImage(item.id)}
                  disabled={deletingImageId === item.id}
                  aria-label={item.video_url ? "Delete video" : "Delete image"}
                  className="absolute right-1.5 top-1.5 rounded-full bg-black/60 p-1.5 text-white opacity-0 transition-opacity hover:bg-rose-500 group-hover:opacity-100 disabled:opacity-50"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
                {item.caption && (
                  <p className="absolute inset-x-0 bottom-0 truncate bg-black/60 px-1.5 py-1 text-[11px] text-white">
                    {item.caption}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </Panel>
    </div>
  );
}
