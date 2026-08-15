"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ArrowLeft } from "lucide-react";
import { authInputClass, authLabelClass } from "@/components/AuthCard";
import { ErrorState, LoadingState } from "@/components/dashboard/DashboardStates";
import { Panel } from "@/components/dashboard/Panel";
import { StringListInput } from "@/components/dashboard/StringListInput";
import { CourseCoverImage } from "@/components/dashboard/course-builder/CourseCoverImage";
import {
  getAdminCourse,
  notifyCourseRecipients,
  updateAdminCourse,
  uploadAdminCourseCoverImage,
  type NotifyAudience,
} from "@/lib/api/adminCourses";
import { ApiError } from "@/lib/api/client";
import { createTag, listCategories, listTags } from "@/lib/api/courses";
import type { Category, CourseDetail, Tag } from "@/lib/api/types";
import { useAuth } from "@/lib/auth/AuthContext";

const STATUS_STYLES: Record<string, string> = {
  draft: "bg-foreground/10 text-foreground/70",
  submitted: "bg-amber-500/10 text-amber-400",
  approved: "bg-teal-400/10 text-teal-400",
  rejected: "bg-rose-500/10 text-rose-400",
  published: "bg-emerald-500/10 text-emerald-400",
  archived: "bg-foreground/10 text-foreground/50",
};

function NotifyPanel({ courseId, token }: { courseId: string; token: string }) {
  const [audience, setAudience] = useState<NotifyAudience>("both");
  const [subject, setSubject] = useState("");
  const [message, setMessage] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sent, setSent] = useState(false);

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    if (!subject.trim() || !message.trim()) return;
    setSending(true);
    setError(null);
    setSent(false);
    try {
      await notifyCourseRecipients(courseId, { audience, subject, message }, token);
      setSent(true);
      setSubject("");
      setMessage("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't send this notification.");
    } finally {
      setSending(false);
    }
  }

  return (
    <form onSubmit={handleSend} className="space-y-4">
      <div>
        <span className={authLabelClass}>Audience</span>
        <div className="mt-1.5 flex gap-2">
          {(["instructor", "students", "both"] as const).map((option) => (
            <label
              key={option}
              className={`cursor-pointer rounded-full border px-3.5 py-1.5 text-xs font-medium capitalize transition-colors ${
                audience === option
                  ? "border-teal-400 bg-teal-400/10 text-teal-400"
                  : "border-border-strong text-foreground/70 hover:bg-surface-hover"
              }`}
            >
              <input
                type="radio"
                name="audience"
                value={option}
                checked={audience === option}
                onChange={() => setAudience(option)}
                className="sr-only"
              />
              {option}
            </label>
          ))}
        </div>
      </div>

      <div>
        <label htmlFor="notify-subject" className={authLabelClass}>
          Subject
        </label>
        <input
          id="notify-subject"
          type="text"
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
          className={authInputClass}
          placeholder="Heads up about your course"
        />
      </div>

      <div>
        <label htmlFor="notify-message" className={authLabelClass}>
          Message
        </label>
        <textarea
          id="notify-message"
          rows={4}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          className={authInputClass}
        />
      </div>

      {error && <p className="text-sm text-rose-400">{error}</p>}
      {sent && (
        <p className="text-sm text-teal-400">
          Sent — recipients get both an in-app notification and an email.
        </p>
      )}

      <button
        type="submit"
        disabled={sending || !subject.trim() || !message.trim()}
        className="rounded-full bg-teal-400 px-5 py-2 text-sm font-semibold text-emerald-950 transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {sending ? "Sending…" : "Send notification"}
      </button>
    </form>
  );
}

export default function AdminCourseEditPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { accessToken } = useAuth();

  const [course, setCourse] = useState<CourseDetail | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [tags, setTags] = useState<Tag[]>([]);
  const [newTagName, setNewTagName] = useState("");
  const [creatingTag, setCreatingTag] = useState(false);

  const [title, setTitle] = useState("");
  const [summary, setSummary] = useState("");
  const [description, setDescription] = useState("");
  const [language, setLanguage] = useState("en");
  const [difficulty, setDifficulty] = useState<"beginner" | "intermediate" | "advanced">(
    "beginner"
  );
  const [priceAmount, setPriceAmount] = useState("0.00");
  const [currency, setCurrency] = useState("USD");
  const [categoryId, setCategoryId] = useState("");
  const [tagIds, setTagIds] = useState<string[]>([]);
  const [prerequisites, setPrerequisites] = useState<string[]>([]);
  const [learningObjectives, setLearningObjectives] = useState<string[]>([]);

  const [loadError, setLoadError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!accessToken) return;
    let cancelled = false;
    Promise.all([getAdminCourse(id, accessToken), listCategories(), listTags()])
      .then(([courseData, categoryList, tagList]) => {
        if (cancelled) return;
        setCourse(courseData);
        setCategories(categoryList);
        setTags(tagList);
        setTitle(courseData.title);
        setSummary(courseData.summary);
        setDescription(courseData.description);
        setLanguage(courseData.language);
        setDifficulty(courseData.difficulty);
        setPriceAmount(courseData.price_amount);
        setCurrency(courseData.currency);
        setCategoryId(courseData.category?.id ?? "");
        setTagIds(courseData.tags.map((t) => t.id));
        setPrerequisites(courseData.prerequisites);
        setLearningObjectives(courseData.learning_objectives);
      })
      .catch((err) => {
        if (!cancelled) {
          setLoadError(err instanceof ApiError ? err.message_ : "Couldn't load this course.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [id, accessToken]);

  function toggleTag(tagId: string) {
    setTagIds((prev) => (prev.includes(tagId) ? prev.filter((i) => i !== tagId) : [...prev, tagId]));
  }

  async function handleCreateTag(event: React.FormEvent) {
    event.preventDefault();
    const name = newTagName.trim();
    if (!accessToken || !name) return;
    setCreatingTag(true);
    try {
      const tag = await createTag(name, accessToken);
      setTags((prev) => (prev.some((t) => t.id === tag.id) ? prev : [...prev, tag]));
      setTagIds((prev) => (prev.includes(tag.id) ? prev : [...prev, tag.id]));
      setNewTagName("");
    } catch (err) {
      setSaveError(err instanceof ApiError ? err.message_ : "Couldn't create that tag.");
    } finally {
      setCreatingTag(false);
    }
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!accessToken || !course || !title.trim() || !categoryId) return;
    setSaving(true);
    setSaveError(null);
    setSaved(false);
    try {
      await updateAdminCourse(
        course.id,
        {
          title,
          summary,
          description,
          language,
          difficulty,
          price_amount: priceAmount,
          currency,
          category_id: categoryId,
          tag_ids: tagIds,
          prerequisites: prerequisites.map((p) => p.trim()).filter(Boolean),
          learning_objectives: learningObjectives.map((o) => o.trim()).filter(Boolean),
        },
        accessToken
      );
      // updateAdminCourse's response is CourseWriteResult (bare category_id/
      // tag_ids, no nested category/tags) — a different shape from the
      // CourseDetail this page's `course` state holds, so merge just the
      // title (the only `course.*` field this form's header displays)
      // from local state instead of replacing the whole object.
      setCourse((prev) => (prev ? { ...prev, title } : prev));
      setSaved(true);
    } catch (err) {
      setSaveError(err instanceof ApiError ? err.message_ : "Couldn't save this course.");
    } finally {
      setSaving(false);
    }
  }

  if (loadError && !course) return <ErrorState message={loadError} />;
  if (!course) return <LoadingState label="Loading course…" />;

  return (
    <div className="mx-auto max-w-2xl space-y-8">
      <div>
        <button
          type="button"
          onClick={() => router.push("/dashboard/courses")}
          className="flex items-center gap-1.5 text-sm text-foreground/50 hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" /> Back to courses
        </button>

        <div className="mt-4 flex flex-wrap items-center gap-3">
          <h1 className="text-2xl font-semibold text-foreground">{course.title}</h1>
          <span
            className={`rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${
              STATUS_STYLES[course.status] ?? ""
            }`}
          >
            {course.status}
          </span>
        </div>
        <p className="mt-2 text-xs text-foreground/40">
          Slug: {course.slug} ·{" "}
          <Link href={`/courses/${course.id}`} className="underline hover:text-foreground/60">
            View public page
          </Link>
        </p>
      </div>

      <Panel title="Course record" subtitle="Editable regardless of status. Curriculum (sections, lessons, quizzes) is managed by the instructor.">
        <form onSubmit={handleSubmit} className="space-y-6">
          {saveError && <div className="rounded-lg bg-red-500/10 p-3 text-sm text-red-400">{saveError}</div>}
          {saved && <p className="text-sm text-teal-400">Saved.</p>}

          <div>
            <span className={authLabelClass}>Cover image</span>
            <div className="mt-1.5">
              <CourseCoverImage
                courseId={course.id}
                coverImage={course.cover_image}
                token={accessToken!}
                uploadFn={uploadAdminCourseCoverImage}
                onUploaded={(coverImage) =>
                  setCourse((prev) => (prev ? { ...prev, cover_image: coverImage } : prev))
                }
              />
            </div>
          </div>

          <div>
            <label htmlFor="title" className={authLabelClass}>
              Title
            </label>
            <input
              id="title"
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className={authInputClass}
            />
          </div>

          <div>
            <label htmlFor="summary" className={authLabelClass}>
              Summary
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
              rows={5}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className={authInputClass}
            />
          </div>

          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <div>
              <label htmlFor="language" className={authLabelClass}>
                Language
              </label>
              <input
                id="language"
                type="text"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className={authInputClass}
              />
            </div>

            <div>
              <label htmlFor="difficulty" className={authLabelClass}>
                Difficulty
              </label>
              <select
                id="difficulty"
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value as typeof difficulty)}
                className={authInputClass}
              >
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
              </select>
            </div>

            <div>
              <label htmlFor="price" className={authLabelClass}>
                Price
              </label>
              <input
                id="price"
                type="number"
                min="0"
                step="0.01"
                value={priceAmount}
                onChange={(e) => setPriceAmount(e.target.value)}
                className={authInputClass}
              />
            </div>

            <div>
              <label htmlFor="currency" className={authLabelClass}>
                Currency
              </label>
              <input
                id="currency"
                type="text"
                maxLength={3}
                value={currency}
                onChange={(e) => setCurrency(e.target.value.toUpperCase())}
                className={authInputClass}
              />
            </div>
          </div>

          <div>
            <label htmlFor="category" className={authLabelClass}>
              Category
            </label>
            <select
              id="category"
              required
              value={categoryId}
              onChange={(e) => setCategoryId(e.target.value)}
              className={authInputClass}
            >
              <option value="" disabled>
                Select a category…
              </option>
              {categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <span className="block text-sm font-medium text-foreground/70">Tags</span>
            {tags.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-2">
                {tags.map((tag) => (
                  <label
                    key={tag.id}
                    className={`cursor-pointer rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
                      tagIds.includes(tag.id)
                        ? "border-teal-400 bg-teal-400/10 text-teal-400"
                        : "border-border-strong text-foreground/70 hover:bg-surface-hover"
                    }`}
                  >
                    <input
                      type="checkbox"
                      className="sr-only"
                      checked={tagIds.includes(tag.id)}
                      onChange={() => toggleTag(tag.id)}
                    />
                    {tag.name}
                  </label>
                ))}
              </div>
            )}
            <div className="mt-2 flex items-center gap-2">
              <input
                type="text"
                value={newTagName}
                onChange={(e) => setNewTagName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleCreateTag(e);
                }}
                placeholder="Add a new tag"
                className={`${authInputClass} max-w-50`}
              />
              <button
                type="button"
                onClick={handleCreateTag}
                disabled={creatingTag || !newTagName.trim()}
                className="rounded-full border border-border-strong px-3 py-1.5 text-xs font-semibold text-foreground/70 transition-colors hover:bg-surface-hover disabled:cursor-not-allowed disabled:opacity-50"
              >
                {creatingTag ? "Adding…" : "Add tag"}
              </button>
            </div>
          </div>

          <StringListInput
            label="Prerequisites"
            placeholder="Basic Python syntax"
            values={prerequisites}
            onChange={setPrerequisites}
          />

          <StringListInput
            label="Learning objectives"
            placeholder="Build a REST API with Django REST Framework"
            values={learningObjectives}
            onChange={setLearningObjectives}
          />

          <button
            type="submit"
            disabled={saving || !title.trim() || !categoryId}
            className="rounded-full bg-teal-400 px-6 py-2.5 text-sm font-semibold text-emerald-950 transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {saving ? "Saving…" : "Save changes"}
          </button>
        </form>
      </Panel>

      <Panel
        title="Notify"
        subtitle="Message this course's instructor and/or its enrolled students. Always sent over both in-app and email."
      >
        <NotifyPanel courseId={course.id} token={accessToken!} />
      </Panel>
    </div>
  );
}
