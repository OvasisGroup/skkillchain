"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { authInputClass, authLabelClass } from "@/components/AuthCard";
import { PageHeader } from "@/components/dashboard/PageHeader";
import { StringListInput } from "@/components/dashboard/StringListInput";
import { ApiError } from "@/lib/api/client";
import { createTag, listCategories, listTags } from "@/lib/api/courses";
import { createCourse } from "@/lib/api/instructorCourses";
import type { Category, Tag } from "@/lib/api/types";
import { useAuth } from "@/lib/auth/AuthContext";

export default function NewCoursePage() {
  const router = useRouter();
  const { accessToken } = useAuth();

  const [categories, setCategories] = useState<Category[]>([]);
  const [tags, setTags] = useState<Tag[]>([]);

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
  const [newTagName, setNewTagName] = useState("");
  const [creatingTag, setCreatingTag] = useState(false);
  const [prerequisites, setPrerequisites] = useState<string[]>([]);
  const [learningObjectives, setLearningObjectives] = useState<string[]>([]);
  const [coverImage, setCoverImage] = useState<File | null>(null);
  // Derived from coverImage rather than its own state+effect pair — the
  // URL itself needs no setState, just a revoke on cleanup, so useMemo
  // (recomputed) + a cleanup-only effect (no setState in its body) is all
  // this needs.
  const coverImagePreview = useMemo(
    () => (coverImage ? URL.createObjectURL(coverImage) : null),
    [coverImage]
  );

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listCategories().then(setCategories).catch(() => {});
    listTags().then(setTags).catch(() => {});
  }, []);

  useEffect(() => {
    return () => {
      if (coverImagePreview) URL.revokeObjectURL(coverImagePreview);
    };
  }, [coverImagePreview]);

  function toggle(ids: string[], setIds: (next: string[]) => void, id: string) {
    setIds(ids.includes(id) ? ids.filter((i) => i !== id) : [...ids, id]);
  }

  async function handleCreateTag(event: React.FormEvent) {
    event.preventDefault();
    const name = newTagName.trim();
    if (!accessToken || !name) return;
    setCreatingTag(true);
    setError(null);
    try {
      const tag = await createTag(name, accessToken);
      setTags((prev) => (prev.some((t) => t.id === tag.id) ? prev : [...prev, tag]));
      setTagIds((prev) => (prev.includes(tag.id) ? prev : [...prev, tag.id]));
      setNewTagName("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't create that tag.");
    } finally {
      setCreatingTag(false);
    }
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!accessToken || !title.trim() || !categoryId) return;
    setSubmitting(true);
    setError(null);
    try {
      const course = await createCourse(
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
          cover_image: coverImage ?? undefined,
        },
        accessToken
      );
      router.push(`/dashboard/instructor/courses/${course.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't create the course.");
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-8">
      <PageHeader
        eyebrow="Instructor"
        title="Create a new course"
        subtitle="Start with the course basics. You'll add sections, lessons, quizzes, and assignments on the next page — the course stays a private draft until you submit it for review."
      />

      <form
        onSubmit={handleSubmit}
        className="space-y-6 rounded-2xl border border-border bg-surface p-6 sm:p-8"
      >
        {error && (
          <div className="rounded-lg bg-red-500/10 p-3 text-sm text-red-400">{error}</div>
        )}

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
            placeholder="Mastering Django: Beginner to Enterprise"
          />
        </div>

        <div>
          <span className={authLabelClass}>Cover image</span>
          <div className="mt-1.5 flex items-center gap-4">
            <div className="flex aspect-video w-40 flex-none items-center justify-center overflow-hidden rounded-lg border border-border-strong bg-surface-hover">
              {coverImagePreview ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={coverImagePreview}
                  alt="Cover preview"
                  className="h-full w-full object-cover"
                />
              ) : (
                <span className="text-xs text-foreground/30">No image</span>
              )}
            </div>
            <label className="cursor-pointer rounded-full bg-teal-400/10 px-3 py-1.5 text-xs font-semibold text-teal-400 hover:bg-teal-400/20">
              {coverImage ? "Change image" : "Upload image"}
              <input
                type="file"
                accept="image/*"
                onChange={(e) => setCoverImage(e.target.files?.[0] ?? null)}
                className="hidden"
              />
            </label>
          </div>
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
            placeholder="One line describing the course"
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
            placeholder="The full course description shown on the course page"
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
                    onChange={() => toggle(tagIds, setTagIds, tag.id)}
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

        <div className="flex gap-3 pt-2">
          <button
            type="submit"
            disabled={submitting || !title.trim() || !categoryId}
            className="rounded-full bg-teal-400 px-6 py-2.5 text-sm font-semibold text-emerald-950 transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {submitting ? "Creating…" : "Create course & continue"}
          </button>
        </div>
      </form>
    </div>
  );
}
