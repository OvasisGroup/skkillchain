"use client";

import { CheckCircle2, CircleDashed, FileText, Video } from "lucide-react";
import { useParams, usePathname, useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import { ErrorState, LoadingState } from "@/components/dashboard/DashboardStates";
import { ApiError } from "@/lib/api/client";
import {
  getCourseCurriculum,
  getLessonContent,
  getProgress,
  listMyCourses,
  updateProgress,
} from "@/lib/api/enrollments";
import { toEmbeddableVideoUrl } from "@/lib/videoEmbed";
import type {
  CurriculumLesson,
  CurriculumSection,
  EnrollmentProgress,
  LessonContent,
  ProgressEntry,
} from "@/lib/api/types";
import { useAuth } from "@/lib/auth/AuthContext";
import { Reveal } from "@/components/animation/Reveal";

// How often (ms) to persist video playback position while it's playing —
// reporting on every `timeupdate` tick would be several requests a second.
const PROGRESS_REPORT_INTERVAL_MS = 5000;

export default function LearnCoursePage() {
  const { courseId } = useParams<{ courseId: string }>();
  const router = useRouter();
  const pathname = usePathname();
  const { accessToken, isAuthenticated, isLoading: authLoading } = useAuth();

  const [courseTitle, setCourseTitle] = useState<string | null>(null);
  const [sections, setSections] = useState<CurriculumSection[] | null>(null);
  const [progress, setProgress] = useState<EnrollmentProgress | null>(null);
  const [selectedLessonId, setSelectedLessonId] = useState<string | null>(null);
  const [content, setContent] = useState<LessonContent | null>(null);
  const [notEnrolled, setNotEnrolled] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [contentError, setContentError] = useState<string | null>(null);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
    }
  }, [authLoading, isAuthenticated, router, pathname]);

  useEffect(() => {
    if (!accessToken) return;
    let cancelled = false;

    async function load() {
      const token = accessToken as string;
      const enrollments = await listMyCourses(token);
      const enrollment = enrollments.results.find((e) => e.course.id === courseId);
      if (!enrollment) {
        if (!cancelled) setNotEnrolled(true);
        return;
      }
      if (cancelled) return;
      setCourseTitle(enrollment.course.title);

      const [curriculum, progressData] = await Promise.all([
        getCourseCurriculum(courseId, token),
        getProgress(enrollment.id, token),
      ]);
      if (cancelled) return;
      setSections(curriculum);
      setProgress(progressData);
      const firstLesson = curriculum.find((s) => s.lessons.length > 0)?.lessons[0];
      if (firstLesson) setSelectedLessonId(firstLesson.id);
    }

    load().catch((err) => {
      if (!cancelled) setError(err instanceof ApiError ? err.message_ : "Couldn't load this course.");
    });

    return () => {
      cancelled = true;
    };
  }, [accessToken, courseId]);

  useEffect(() => {
    if (!accessToken || !selectedLessonId) return;
    // content/contentError are reset in the sidebar's onSelect handler
    // above (not synchronously here), so switching lessons doesn't
    // briefly flash the previous lesson's content while this fetch runs.
    // The other setSelectedLessonId call site (auto-selecting the first
    // lesson on load) needs no reset — content/contentError are still at
    // their initial null there.
    let cancelled = false;

    getLessonContent(selectedLessonId, accessToken)
      .then((data) => {
        if (!cancelled) setContent(data);
      })
      .catch((err) => {
        if (!cancelled) {
          setContentError(err instanceof ApiError ? err.message_ : "Couldn't load this lesson.");
        }
      });

    return () => {
      cancelled = true;
    };
  }, [accessToken, selectedLessonId]);

  const progressByLesson = useMemo(() => {
    const map: Record<string, ProgressEntry> = {};
    progress?.lessons.forEach((entry) => {
      map[entry.lesson_id] = entry;
    });
    return map;
  }, [progress]);

  function applyLocalProgress(lessonId: string, percentComplete: number, lastPositionSeconds: number) {
    setProgress((prev) => {
      if (!prev) return prev;
      const existingIndex = prev.lessons.findIndex((l) => l.lesson_id === lessonId);
      const lessonTitle =
        sections?.flatMap((s) => s.lessons).find((l) => l.id === lessonId)?.title ?? "";
      const nextEntry: ProgressEntry = {
        lesson_id: lessonId,
        lesson_title: lessonTitle,
        percent_complete: percentComplete,
        last_position_seconds: lastPositionSeconds,
        last_viewed_at: new Date().toISOString(),
      };
      const lessons =
        existingIndex >= 0
          ? prev.lessons.map((l, i) => (i === existingIndex ? nextEntry : l))
          : [...prev.lessons, nextEntry];
      const overall = Math.round(
        lessons.reduce((sum, l) => sum + l.percent_complete, 0) / (sections?.flatMap((s) => s.lessons).length || 1)
      );
      return { ...prev, lessons, overall_percent: Math.min(overall, 100) };
    });
  }

  function reportProgress(lessonId: string, percentComplete: number, lastPositionSeconds: number) {
    if (!accessToken) return;
    applyLocalProgress(lessonId, percentComplete, lastPositionSeconds);
    updateProgress(
      { lesson_id: lessonId, percent_complete: percentComplete, last_position_seconds: lastPositionSeconds },
      accessToken
    ).catch(() => {
      // Best-effort — the next progress tick (or a manual "mark complete")
      // will retry implicitly. Not worth surfacing a UI error for this.
    });
  }

  if (authLoading || (!error && !notEnrolled && !sections)) {
    return (
      <div className="mx-auto max-w-6xl px-6 py-10">
        <LoadingState label="Loading your course…" />
      </div>
    );
  }

  if (notEnrolled) {
    return (
      <div className="mx-auto max-w-2xl px-6 py-16 text-center">
        <h1 className="text-xl font-semibold text-foreground">You&apos;re not enrolled in this course</h1>
        <p className="mt-2 text-sm text-foreground/60">
          Enroll first to access its lessons and track your progress.
        </p>
        <a
          href={`/courses/${courseId}`}
          className="mt-6 inline-block rounded-full bg-teal-400 px-6 py-2.5 text-sm font-semibold text-emerald-950 transition-opacity hover:opacity-90"
        >
          View course
        </a>
      </div>
    );
  }

  if (error) return <ErrorState message={error} />;

  const allLessons = sections!.flatMap((s) => s.lessons);
  const selectedLesson = allLessons.find((l) => l.id === selectedLessonId) ?? null;

  return (
    <div className="mx-auto max-w-6xl px-6 py-8">
      <Reveal className="mb-6">
        <p className="text-sm font-semibold uppercase tracking-wider text-lime-400">Learning</p>
        <h1 className="mt-1 text-2xl font-semibold text-foreground">{courseTitle}</h1>
        <div className="mt-3 flex items-center gap-3">
          <div className="h-2 w-full max-w-sm overflow-hidden rounded-full bg-surface-hover">
            <div
              className="h-full rounded-full bg-teal-400 transition-all"
              style={{ width: `${progress?.overall_percent ?? 0}%` }}
            />
          </div>
          <span className="text-xs text-foreground/50">{progress?.overall_percent ?? 0}% complete</span>
        </div>
      </Reveal>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[280px_1fr]">
        <aside className="space-y-4 lg:order-1 order-2">
          {sections!.map((section) => (
            <div key={section.id}>
              <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-foreground/40">
                {section.title}
              </p>
              <ul className="space-y-1">
                {section.lessons.map((lesson) => (
                  <LessonSidebarRow
                    key={lesson.id}
                    lesson={lesson}
                    isSelected={lesson.id === selectedLessonId}
                    percentComplete={progressByLesson[lesson.id]?.percent_complete ?? 0}
                    onSelect={() => {
                      setSelectedLessonId(lesson.id);
                      setContent(null);
                      setContentError(null);
                    }}
                  />
                ))}
              </ul>
            </div>
          ))}
        </aside>

        <main className="order-1 lg:order-2">
          {selectedLesson ? (
            <LessonViewer
              key={selectedLesson.id}
              lesson={selectedLesson}
              content={content}
              contentError={contentError}
              percentComplete={progressByLesson[selectedLesson.id]?.percent_complete ?? 0}
              onProgress={(percent, position) => reportProgress(selectedLesson.id, percent, position)}
            />
          ) : (
            <p className="text-sm text-foreground/50">This course has no lessons yet.</p>
          )}
        </main>
      </div>
    </div>
  );
}

function LessonSidebarRow({
  lesson,
  isSelected,
  percentComplete,
  onSelect,
}: {
  lesson: CurriculumLesson;
  isSelected: boolean;
  percentComplete: number;
  onSelect: () => void;
}) {
  const Icon = lesson.lesson_type === "video" ? Video : lesson.lesson_type === "pdf" ? FileText : CircleDashed;
  return (
    <li>
      <button
        type="button"
        onClick={onSelect}
        className={`flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm transition-colors ${
          isSelected ? "bg-teal-400/10 text-teal-400" : "text-foreground/70 hover:bg-surface-hover"
        }`}
      >
        {percentComplete >= 100 ? (
          <CheckCircle2 className="h-4 w-4 flex-none text-emerald-400" />
        ) : (
          <Icon className="h-4 w-4 flex-none opacity-60" />
        )}
        <span className="min-w-0 flex-1 truncate">{lesson.title}</span>
        {percentComplete > 0 && percentComplete < 100 && (
          <span className="flex-none text-xs text-foreground/40">{percentComplete}%</span>
        )}
      </button>
    </li>
  );
}

function LessonViewer({
  lesson,
  content,
  contentError,
  percentComplete,
  onProgress,
}: {
  lesson: CurriculumLesson;
  content: LessonContent | null;
  contentError: string | null;
  percentComplete: number;
  onProgress: (percentComplete: number, lastPositionSeconds: number) => void;
}) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const lastReportedAt = useRef(0);
  const hasReportedView = useRef(false);

  useEffect(() => {
    lastReportedAt.current = 0;
    hasReportedView.current = false;
  }, [lesson.id]);

  useEffect(() => {
    const marksViewedOnLoad = lesson.lesson_type === "pdf" || lesson.lesson_type === "article";
    if (marksViewedOnLoad && content && !hasReportedView.current && percentComplete === 0) {
      hasReportedView.current = true;
      onProgress(10, 0);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lesson.lesson_type, content]);

  const videoEmbedUrl = content?.video_url ? toEmbeddableVideoUrl(content.video_url) : null;

  function handleTimeUpdate() {
    const video = videoRef.current;
    if (!video || !video.duration) return;
    const now = Date.now();
    if (now - lastReportedAt.current < PROGRESS_REPORT_INTERVAL_MS) return;
    lastReportedAt.current = now;
    const percent = Math.min(99, Math.round((video.currentTime / video.duration) * 100));
    onProgress(percent, Math.floor(video.currentTime));
  }

  function handleEnded() {
    const video = videoRef.current;
    onProgress(100, video ? Math.floor(video.duration) : lesson.duration_seconds);
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-4">
        <h2 className="text-lg font-semibold text-foreground">{lesson.title}</h2>
        <button
          type="button"
          onClick={() => onProgress(100, lesson.duration_seconds)}
          disabled={percentComplete >= 100}
          className="flex-none rounded-full border border-border-strong px-3 py-1 text-xs font-semibold text-foreground/80 transition-colors hover:bg-surface-hover disabled:cursor-not-allowed disabled:opacity-50"
        >
          {percentComplete >= 100 ? "Completed" : "Mark as complete"}
        </button>
      </div>

      {contentError && <ErrorState message={contentError} />}

      {!content && !contentError && <LoadingState label="Loading lesson…" />}

      {content && lesson.lesson_type === "video" && content.content_file && (
        <video
          ref={videoRef}
          src={content.content_file}
          controls
          className="aspect-video w-full rounded-xl border border-border bg-black"
          onTimeUpdate={handleTimeUpdate}
          onEnded={handleEnded}
        />
      )}

      {content && lesson.lesson_type === "video" && !content.content_file && content.video_url && (
        videoEmbedUrl ? (
          <iframe
            src={videoEmbedUrl}
            title={lesson.title}
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
            className="aspect-video w-full rounded-xl border border-border"
          />
        ) : (
          // Not a recognized YouTube/Vimeo page — treat as a direct media
          // file URL (e.g. an .mp4 hosted elsewhere) and play it natively.
          <video
            ref={videoRef}
            src={content.video_url}
            controls
            className="aspect-video w-full rounded-xl border border-border bg-black"
            onTimeUpdate={handleTimeUpdate}
            onEnded={handleEnded}
          />
        )
      )}

      {content && lesson.lesson_type === "pdf" && content.content_file && (
        <iframe
          src={content.content_file}
          title={lesson.title}
          className="h-[75vh] w-full rounded-xl border border-border"
        />
      )}

      {content &&
        lesson.lesson_type === "video" &&
        !content.content_file &&
        !content.video_url && (
          <p className="rounded-xl border border-dashed border-border p-8 text-center text-sm text-foreground/50">
            The instructor hasn&apos;t added a video for this lesson yet.
          </p>
        )}

      {content && lesson.lesson_type === "pdf" && !content.content_file && (
        <p className="rounded-xl border border-dashed border-border p-8 text-center text-sm text-foreground/50">
          The instructor hasn&apos;t uploaded a PDF for this lesson yet.
        </p>
      )}

      {content && lesson.lesson_type === "article" && content.article_body && (
        <div className="whitespace-pre-wrap rounded-xl border border-border bg-surface p-6 text-sm leading-relaxed text-foreground/80">
          {content.article_body}
        </div>
      )}

      {content && lesson.lesson_type === "article" && !content.article_body && (
        <p className="rounded-xl border border-dashed border-border p-8 text-center text-sm text-foreground/50">
          The instructor hasn&apos;t written this article yet.
        </p>
      )}

      {content && (lesson.lesson_type === "quiz" || lesson.lesson_type === "assignment") && (
        <p className="rounded-xl border border-dashed border-border p-8 text-center text-sm text-foreground/50">
          This lesson type doesn&apos;t have a dedicated viewer yet — use &quot;Mark as complete&quot; to track
          your progress through it.
        </p>
      )}
    </div>
  );
}
