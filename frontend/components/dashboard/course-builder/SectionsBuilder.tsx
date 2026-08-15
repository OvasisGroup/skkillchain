"use client";

import { Plus } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { authInputClass } from "@/components/AuthCard";
import { ApiError } from "@/lib/api/client";
import { createLesson, createSection, listLessons, uploadLessonContent } from "@/lib/api/content";
import type { Lesson, Section } from "@/lib/api/types";

function LessonContentUpload({
  lesson,
  token,
  onUploaded,
}: {
  lesson: Lesson;
  token: string;
  onUploaded: (lesson: Lesson) => void;
}) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleFile(file: File | undefined) {
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const updated = await uploadLessonContent(lesson.id, file, token);
      onUploaded(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't upload the file.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <span className="flex items-center gap-2">
      <label className="cursor-pointer rounded-full bg-amber-500/10 px-2.5 py-0.5 text-xs font-medium text-amber-400 hover:bg-amber-500/20">
        {uploading ? "Uploading…" : "Attach file"}
        <input
          type="file"
          accept={lesson.lesson_type === "video" ? "video/*" : "application/pdf"}
          disabled={uploading}
          onChange={(e) => handleFile(e.target.files?.[0])}
          className="hidden"
        />
      </label>
      {error && <span className="text-xs text-rose-400">{error}</span>}
    </span>
  );
}

function LessonForm({
  sectionId,
  token,
  nextSortOrder,
  onCreated,
  onCancel,
}: {
  sectionId: string;
  token: string;
  nextSortOrder: number;
  onCreated: (lesson: Lesson) => void;
  onCancel: () => void;
}) {
  const [title, setTitle] = useState("");
  const [lessonType, setLessonType] = useState<Lesson["lesson_type"]>("video");
  const [durationSeconds, setDurationSeconds] = useState("300");
  const [isPreview, setIsPreview] = useState(false);
  const [contentFile, setContentFile] = useState<File | null>(null);
  const [videoSource, setVideoSource] = useState<"file" | "url">("file");
  const [videoUrl, setVideoUrl] = useState("");
  const [articleBody, setArticleBody] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const showFileInput = lessonType === "pdf" || (lessonType === "video" && videoSource === "file");
  const showVideoUrlInput = lessonType === "video" && videoSource === "url";
  const showArticleInput = lessonType === "article";

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!title.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      const lesson = await createLesson(
        sectionId,
        {
          title,
          lesson_type: lessonType,
          sort_order: nextSortOrder,
          duration_seconds: Number(durationSeconds) || 0,
          is_preview: isPreview,
          content_file: showFileInput && contentFile ? contentFile : undefined,
          video_url: showVideoUrlInput && videoUrl.trim() ? videoUrl.trim() : undefined,
          article_body: showArticleInput && articleBody.trim() ? articleBody.trim() : undefined,
        },
        token
      );
      onCreated(lesson);
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't create the lesson.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="mt-3 space-y-3 rounded-lg border border-border-strong bg-background/40 p-3"
    >
      <input
        type="text"
        required
        autoFocus
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="Lesson title"
        className={authInputClass}
      />
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
        <select
          value={lessonType}
          onChange={(e) => setLessonType(e.target.value as Lesson["lesson_type"])}
          className={authInputClass}
        >
          <option value="video">Video</option>
          <option value="pdf">PDF</option>
          <option value="article">Article</option>
          <option value="quiz">Quiz</option>
          <option value="assignment">Assignment</option>
        </select>
        <input
          type="number"
          min="0"
          value={durationSeconds}
          onChange={(e) => setDurationSeconds(e.target.value)}
          placeholder="Duration (s)"
          className={authInputClass}
        />
        <label className="flex items-center gap-2 text-sm text-foreground/70">
          <input
            type="checkbox"
            checked={isPreview}
            onChange={(e) => setIsPreview(e.target.checked)}
            className="h-4 w-4 rounded border-border-strong"
          />
          Free preview
        </label>
      </div>
      {lessonType === "video" && (
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setVideoSource("file")}
            className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
              videoSource === "file"
                ? "border-teal-400 bg-teal-400/10 text-teal-400"
                : "border-border-strong text-foreground/60 hover:bg-surface-hover"
            }`}
          >
            Upload file
          </button>
          <button
            type="button"
            onClick={() => setVideoSource("url")}
            className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
              videoSource === "url"
                ? "border-teal-400 bg-teal-400/10 text-teal-400"
                : "border-border-strong text-foreground/60 hover:bg-surface-hover"
            }`}
          >
            Video URL
          </button>
        </div>
      )}
      {showFileInput && (
        <div>
          <input
            type="file"
            accept={lessonType === "video" ? "video/*" : "application/pdf"}
            onChange={(e) => setContentFile(e.target.files?.[0] ?? null)}
            className="block w-full text-sm text-foreground/70 file:mr-3 file:rounded-full file:border-0 file:bg-teal-400/10 file:px-3 file:py-1.5 file:text-xs file:font-semibold file:text-teal-400 hover:file:bg-teal-400/20"
          />
          <p className="mt-1 text-xs text-foreground/40">
            Optional here — you can attach the {lessonType === "video" ? "video" : "PDF"} file
            now or come back later.
          </p>
        </div>
      )}
      {showVideoUrlInput && (
        <div>
          <input
            type="url"
            value={videoUrl}
            onChange={(e) => setVideoUrl(e.target.value)}
            placeholder="https://www.youtube.com/watch?v=… or any direct video URL"
            className={authInputClass}
          />
          <p className="mt-1 text-xs text-foreground/40">
            YouTube, Vimeo, or a direct link to a video file — optional here, you can add it
            later too.
          </p>
        </div>
      )}
      {showArticleInput && (
        <div>
          <textarea
            rows={6}
            value={articleBody}
            onChange={(e) => setArticleBody(e.target.value)}
            placeholder="Write the lesson content here…"
            className={authInputClass}
          />
          <p className="mt-1 text-xs text-foreground/40">
            Optional here — you can write the article now or come back later.
          </p>
        </div>
      )}
      {error && <p className="text-sm text-rose-400">{error}</p>}
      <div className="flex gap-2">
        <button
          type="submit"
          disabled={submitting || !title.trim()}
          className="rounded-full bg-teal-400 px-4 py-1.5 text-xs font-semibold text-emerald-950 transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {submitting ? "Adding…" : "Add lesson"}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="text-xs text-foreground/50 hover:text-foreground"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}

export function SectionsBuilder({
  courseId,
  token,
  sections,
  onSectionCreated,
}: {
  courseId: string;
  token: string;
  sections: Section[];
  onSectionCreated: (section: Section) => void;
}) {
  const [lessons, setLessons] = useState<Record<string, Lesson[]>>({});
  const [error, setError] = useState<string | null>(null);
  const fetchedIds = useRef<Set<string>>(new Set());

  const [newSectionTitle, setNewSectionTitle] = useState("");
  const [addingSection, setAddingSection] = useState(false);
  const [openLessonFormFor, setOpenLessonFormFor] = useState<string | null>(null);

  useEffect(() => {
    const toFetch = sections.filter((section) => !fetchedIds.current.has(section.id));
    if (toFetch.length === 0) return;
    let cancelled = false;

    Promise.all(toFetch.map((section) => listLessons(section.id, token)))
      .then((results) => {
        if (cancelled) return;
        // Only mark as fetched once the request actually lands — marking it
        // beforehand means React 18 Strict Mode's dev-only double-invoke
        // skips the second (real) run because the id already looks fetched,
        // while the first run's result gets discarded by `cancelled`.
        toFetch.forEach((section) => fetchedIds.current.add(section.id));
        setLessons((prev) => {
          const next = { ...prev };
          toFetch.forEach((section, index) => {
            next[section.id] = results[index];
          });
          return next;
        });
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof ApiError ? err.message_ : "Couldn't load lessons.");
      });

    return () => {
      cancelled = true;
    };
  }, [sections, token]);

  async function handleAddSection(event: React.FormEvent) {
    event.preventDefault();
    if (!newSectionTitle.trim()) return;
    setAddingSection(true);
    setError(null);
    try {
      const section = await createSection(
        courseId,
        { title: newSectionTitle, sort_order: sections.length },
        token
      );
      fetchedIds.current.add(section.id);
      setLessons((prev) => ({ ...prev, [section.id]: [] }));
      onSectionCreated(section);
      setNewSectionTitle("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't create the section.");
    } finally {
      setAddingSection(false);
    }
  }

  function handleLessonCreated(sectionId: string, lesson: Lesson) {
    setLessons((prev) => ({ ...prev, [sectionId]: [...(prev[sectionId] ?? []), lesson] }));
    setOpenLessonFormFor(null);
  }

  function handleLessonUpdated(sectionId: string, updated: Lesson) {
    setLessons((prev) => ({
      ...prev,
      [sectionId]: (prev[sectionId] ?? []).map((l) => (l.id === updated.id ? updated : l)),
    }));
  }

  return (
    <div className="space-y-4">
      {error && <p className="text-sm text-rose-400">{error}</p>}

      {sections.length === 0 && (
        <p className="text-sm text-foreground/50">No sections yet — add your first one below.</p>
      )}

      {sections.map((section) => (
        <div key={section.id} className="rounded-xl border border-border bg-surface p-4">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-foreground">{section.title}</h3>
            <button
              type="button"
              onClick={() =>
                setOpenLessonFormFor(openLessonFormFor === section.id ? null : section.id)
              }
              className="flex items-center gap-1 text-xs font-semibold text-teal-400 hover:text-teal-300"
            >
              <Plus className="h-3.5 w-3.5" /> Add lesson
            </button>
          </div>

          {(lessons[section.id]?.length ?? 0) > 0 && (
            <ul className="mt-3 space-y-1.5">
              {lessons[section.id].map((lesson) => (
                <li
                  key={lesson.id}
                  className="flex items-center justify-between rounded-lg bg-surface-hover px-3 py-2 text-sm"
                >
                  <span className="text-foreground/80">{lesson.title}</span>
                  <span className="flex items-center gap-2">
                    <span className="text-xs uppercase tracking-wide text-foreground/40">
                      {lesson.lesson_type}
                      {lesson.is_preview ? " · preview" : ""}
                    </span>
                    {(lesson.lesson_type === "video" || lesson.lesson_type === "pdf") &&
                      (lesson.content_file ? (
                        <span className="text-xs text-teal-400">File attached</span>
                      ) : lesson.video_url ? (
                        <span className="text-xs text-teal-400">Video URL set</span>
                      ) : (
                        <LessonContentUpload
                          lesson={lesson}
                          token={token}
                          onUploaded={(updated) => handleLessonUpdated(section.id, updated)}
                        />
                      ))}
                    {lesson.lesson_type === "article" &&
                      (lesson.article_body ? (
                        <span className="text-xs text-teal-400">Article written</span>
                      ) : (
                        <span className="text-xs text-foreground/40">No content yet</span>
                      ))}
                  </span>
                </li>
              ))}
            </ul>
          )}

          {openLessonFormFor === section.id && (
            <LessonForm
              sectionId={section.id}
              token={token}
              nextSortOrder={lessons[section.id]?.length ?? 0}
              onCreated={(lesson) => handleLessonCreated(section.id, lesson)}
              onCancel={() => setOpenLessonFormFor(null)}
            />
          )}
        </div>
      ))}

      <form onSubmit={handleAddSection} className="flex items-center gap-2">
        <input
          type="text"
          value={newSectionTitle}
          onChange={(e) => setNewSectionTitle(e.target.value)}
          placeholder="New section title"
          className={authInputClass}
        />
        <button
          type="submit"
          disabled={addingSection || !newSectionTitle.trim()}
          className="whitespace-nowrap rounded-full bg-teal-400 px-4 py-2 text-xs font-semibold text-emerald-950 transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {addingSection ? "Adding…" : "Add section"}
        </button>
      </form>
    </div>
  );
}
