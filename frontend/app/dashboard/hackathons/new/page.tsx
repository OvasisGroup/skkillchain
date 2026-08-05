"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { authInputClass, authLabelClass } from "@/components/AuthCard";
import { PageHeader } from "@/components/dashboard/PageHeader";
import { ApiError } from "@/lib/api/client";
import { createHackathon } from "@/lib/api/organizerHackathons";
import type { HackathonHostType } from "@/lib/api/types";
import { useAuth } from "@/lib/auth/AuthContext";

export default function NewHackathonPage() {
  const router = useRouter();
  const { accessToken } = useAuth();

  const [title, setTitle] = useState("");
  const [hostType, setHostType] = useState<HackathonHostType>("internal");
  const [partnerName, setPartnerName] = useState("");
  const [partnerUrl, setPartnerUrl] = useState("");
  const [summary, setSummary] = useState("");
  const [description, setDescription] = useState("");
  const [requirements, setRequirements] = useState("");
  const [prizeSummary, setPrizeSummary] = useState("");
  const [registrationDeadline, setRegistrationDeadline] = useState("");
  const [submissionDeadline, setSubmissionDeadline] = useState("");
  const [startsAt, setStartsAt] = useState("");
  const [endsAt, setEndsAt] = useState("");
  const [capacity, setCapacity] = useState("");

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!accessToken || !title.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      const hackathon = await createHackathon(
        {
          title,
          host_type: hostType,
          partner_name: hostType === "partner" ? partnerName : undefined,
          partner_url: hostType === "partner" ? partnerUrl : undefined,
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
      router.push(`/dashboard/hackathons/${hackathon.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't create the hackathon.");
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-8">
      <PageHeader
        eyebrow="Hackathons"
        title="Post a new hackathon"
        subtitle="Host it internally, or in partnership with another organization. It stays a private draft until you publish it."
      />

      <form
        onSubmit={handleSubmit}
        className="space-y-6 rounded-2xl border border-border bg-surface p-6 sm:p-8"
      >
        {error && <div className="rounded-lg bg-red-500/10 p-3 text-sm text-red-400">{error}</div>}

        <div>
          <label htmlFor="title" className={authLabelClass}>
            Title
          </label>
          <input
            id="title"
            type="text"
            required
            autoFocus
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className={authInputClass}
            placeholder="SkillChain Global AI Hackathon"
          />
        </div>

        <div>
          <span className={authLabelClass}>Host</span>
          <div className="mt-1.5 flex gap-2">
            {(["internal", "partner"] as const).map((option) => (
              <button
                key={option}
                type="button"
                onClick={() => setHostType(option)}
                className={`flex-1 rounded-lg border px-3.5 py-2.5 text-sm font-medium capitalize transition-colors ${
                  hostType === option
                    ? "border-teal-400 bg-teal-400/10 text-teal-400"
                    : "border-border-strong text-foreground/70 hover:bg-surface-hover"
                }`}
              >
                {option}
              </button>
            ))}
          </div>
        </div>

        {hostType === "partner" && (
          <>
            <div>
              <label htmlFor="partnerName" className={authLabelClass}>
                Partner organization
              </label>
              <input
                id="partnerName"
                type="text"
                required
                value={partnerName}
                onChange={(e) => setPartnerName(e.target.value)}
                className={authInputClass}
                placeholder="Acme Labs"
              />
            </div>
            <div>
              <label htmlFor="partnerUrl" className={authLabelClass}>
                Partner website (optional)
              </label>
              <input
                id="partnerUrl"
                type="url"
                value={partnerUrl}
                onChange={(e) => setPartnerUrl(e.target.value)}
                className={authInputClass}
                placeholder="https://acmelabs.example.com"
              />
            </div>
          </>
        )}

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
            placeholder="Build an AI-powered learning tool in 48 hours."
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
            placeholder="Teams of up to 4. Original work only. Must submit a public repo."
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

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-full bg-teal-400 px-6 py-3 text-sm font-semibold text-emerald-950 transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {submitting ? "Creating…" : "Create hackathon"}
        </button>
      </form>
    </div>
  );
}
