"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { authInputClass, authLabelClass } from "@/components/AuthCard";
import { PageHeader } from "@/components/dashboard/PageHeader";
import { StringListInput } from "@/components/dashboard/StringListInput";
import { createAdminCourse } from "@/lib/api/adminCourses";
import { listUsers } from "@/lib/api/admin";
import { ApiError } from "@/lib/api/client";
import { createTag, listCategories, listTags } from "@/lib/api/courses";
import type { AdminUser, Category, Tag } from "@/lib/api/types";
import { useAuth } from "@/lib/auth/AuthContext";

function InstructorPicker({
  token,
  selected,
  onSelect,
}: {
  token: string;
  selected: AdminUser | null;
  onSelect: (user: AdminUser | null) => void;
}) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<AdminUser[]>([]);
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    // Stale results from a previous query are harmless left in state —
    // the dropdown below only renders them while `query.trim()` is
    // truthy, and this effect never fires that dropdown-hiding branch's
    // opposite case with results still relevant to the old query.
    if (selected || !query.trim()) {
      return;
    }
    let cancelled = false;
    const timer = setTimeout(() => {
      listUsers(token, { role: "instructor", email: query.trim() })
        .then((page) => {
          if (!cancelled) setResults(page.results);
        })
        .catch(() => {})
        .finally(() => {
          if (!cancelled) setSearching(false);
        });
    }, 300);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [query, selected, token]);

  if (selected) {
    return (
      <div className="flex items-center justify-between rounded-lg border border-border-strong bg-surface-hover px-3.5 py-2.5">
        <span className="text-sm text-foreground">{selected.email}</span>
        <button
          type="button"
          onClick={() => onSelect(null)}
          className="text-xs font-semibold text-teal-400 hover:text-teal-300"
        >
          Change
        </button>
      </div>
    );
  }

  return (
    <div className="relative">
      <input
        type="text"
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          setSearching(Boolean(e.target.value.trim()));
        }}
        placeholder="Search instructors by email…"
        className={authInputClass}
      />
      {(searching || results.length > 0) && query.trim() && (
        <div className="absolute z-10 mt-1 w-full overflow-hidden rounded-lg border border-border-strong bg-surface shadow-lg">
          {searching && <p className="px-3.5 py-2 text-xs text-foreground/50">Searching…</p>}
          {!searching && results.length === 0 && (
            <p className="px-3.5 py-2 text-xs text-foreground/50">
              No instructor found for that email.
            </p>
          )}
          {results.map((user) => (
            <button
              key={user.id}
              type="button"
              onClick={() => {
                onSelect(user);
                setQuery("");
              }}
              className="block w-full px-3.5 py-2 text-left text-sm text-foreground hover:bg-surface-hover"
            >
              {user.email}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default function NewAdminCoursePage() {
  const router = useRouter();
  const { accessToken } = useAuth();

  const [owner, setOwner] = useState<AdminUser | null>(null);
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

  function toggleTag(id: string) {
    setTagIds((prev) => (prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]));
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
    if (!accessToken || !owner || !title.trim() || !categoryId) return;
    setSubmitting(true);
    setError(null);
    try {
      const course = await createAdminCourse(
        {
          owner_id: owner.id,
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
      router.push(`/dashboard/courses/${course.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't create the course.");
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-8">
      <PageHeader
        eyebrow="Admin"
        title="Create a course for an instructor"
        subtitle="Creates a private draft owned by the instructor you pick — identical to a course they'd create themselves. They can then build out sections, lessons, and quizzes from their own dashboard."
      />

      <form
        onSubmit={handleSubmit}
        className="space-y-6 rounded-2xl border border-border bg-surface p-6 sm:p-8"
      >
        {error && <div className="rounded-lg bg-red-500/10 p-3 text-sm text-red-400">{error}</div>}

        <div>
          <span className={authLabelClass}>Instructor</span>
          <div className="mt-1.5">
            {accessToken && (
              <InstructorPicker token={accessToken} selected={owner} onSelect={setOwner} />
            )}
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

        <div className="flex gap-3 pt-2">
          <button
            type="submit"
            disabled={submitting || !owner || !title.trim() || !categoryId}
            className="rounded-full bg-teal-400 px-6 py-2.5 text-sm font-semibold text-emerald-950 transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {submitting ? "Creating…" : "Create course"}
          </button>
        </div>
      </form>
    </div>
  );
}
