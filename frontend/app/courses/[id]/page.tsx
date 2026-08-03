import { BookOpen, Clock, Globe2, Layers } from "lucide-react";
import Link from "next/link";
import { notFound } from "next/navigation";
import { CourseDiscussion } from "@/components/CourseDiscussion";
import { CourseLiveSessions } from "@/components/CourseLiveSessions";
import { EnrollButton } from "@/components/EnrollButton";
import { ApiError } from "@/lib/api/client";
import { getCourse, getCoursePreview } from "@/lib/api/courses";
import { listCourseDiscussions } from "@/lib/api/discussions";
import { listCourseLiveSessions } from "@/lib/api/liveSessions";
import type { CourseDetail, DiscussionPost, LiveSession, PreviewSection } from "@/lib/api/types";
import { SITE_NAME, absoluteUrl } from "@/lib/seo";

const DIFFICULTY_STYLES: Record<CourseDetail["difficulty"], string> = {
  beginner: "bg-emerald-500/10 text-emerald-400",
  intermediate: "bg-amber-500/10 text-amber-400",
  advanced: "bg-rose-500/10 text-rose-400",
};

function formatDuration(totalSeconds: number): string {
  const minutes = Math.round(totalSeconds / 60);
  if (minutes < 1) return "<1 min";
  if (minutes < 60) return `${minutes} min`;
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  return remainingMinutes ? `${hours}h ${remainingMinutes}m` : `${hours}h`;
}

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  try {
    const course = await getCourse(id);
    const canonical = `/courses/${course.id}`;
    return {
      title: course.title,
      description: course.summary,
      alternates: { canonical },
      openGraph: {
        type: "website",
        url: absoluteUrl(canonical),
        title: course.title,
        description: course.summary,
        ...(course.cover_image ? { images: [{ url: course.cover_image }] } : {}),
      },
      twitter: {
        card: "summary_large_image",
        title: course.title,
        description: course.summary,
        ...(course.cover_image ? { images: [course.cover_image] } : {}),
      },
    };
  } catch {
    return { title: "Course" };
  }
}

function courseJsonLd(course: CourseDetail) {
  return {
    "@context": "https://schema.org",
    "@type": "Course",
    name: course.title,
    description: course.summary,
    url: absoluteUrl(`/courses/${course.id}`),
    ...(course.cover_image ? { image: course.cover_image } : {}),
    inLanguage: course.language,
    provider: {
      "@type": "Organization",
      name: SITE_NAME,
      sameAs: absoluteUrl("/"),
    },
    offers: {
      "@type": "Offer",
      price: course.price_amount,
      priceCurrency: course.currency,
      availability: "https://schema.org/InStock",
      url: absoluteUrl(`/courses/${course.id}`),
    },
  };
}

export default async function CourseDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  let course: CourseDetail;
  try {
    course = await getCourse(id);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) {
      notFound();
    }
    throw err;
  }

  let preview: PreviewSection[] = [];
  try {
    preview = await getCoursePreview(id);
  } catch {
    // Preview is a nice-to-have; the course page still works without it.
    preview = [];
  }

  let liveSessions: LiveSession[] = [];
  try {
    liveSessions = await listCourseLiveSessions(id);
  } catch {
    liveSessions = [];
  }

  let discussionPosts: DiscussionPost[] = [];
  try {
    discussionPosts = (await listCourseDiscussions(id)).results;
  } catch {
    discussionPosts = [];
  }

  const isFree = Number(course.price_amount) === 0;

  return (
    <div className="mx-auto max-w-7xl px-6 py-16">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(courseJsonLd(course)) }}
      />
      <nav className="text-sm text-foreground/40">
        <Link href="/courses" className="hover:text-foreground">
          Courses
        </Link>
        <span className="mx-2">/</span>
        <span className="text-foreground">{course.title}</span>
      </nav>

      <div className="mt-8 grid grid-cols-1 gap-12 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <div className="flex flex-wrap items-center gap-2">
            <span
              className={`rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${DIFFICULTY_STYLES[course.difficulty]}`}
            >
              {course.difficulty}
            </span>
            {course.category && (
              <span className="rounded-full bg-surface-hover px-2.5 py-0.5 text-xs font-medium text-foreground/70">
                {course.category.name}
              </span>
            )}
          </div>

          <h1 className="mt-4 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            {course.title}
          </h1>
          <p className="mt-4 text-lg leading-8 text-foreground/60">
            {course.summary}
          </p>

          <div className="mt-6 flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-foreground/50">
            <span>
              Taught by <span className="font-medium text-foreground">{course.instructor.email}</span>
            </span>
            <span className="flex items-center gap-1.5">
              <Globe2 className="h-4 w-4" />
              {course.language.toUpperCase()}
            </span>
          </div>

          {course.description && (
            <div className="mt-10">
              <h2 className="text-lg font-semibold text-foreground">
                About this course
              </h2>
              <p className="mt-3 whitespace-pre-line text-sm leading-7 text-foreground/60">
                {course.description}
              </p>
            </div>
          )}

          {course.learning_objectives.length > 0 && (
            <div className="mt-10">
              <h2 className="text-lg font-semibold text-foreground">
                What you&apos;ll learn
              </h2>
              <ul className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
                {course.learning_objectives.map((objective) => (
                  <li
                    key={objective}
                    className="flex items-start gap-2 text-sm text-foreground/70"
                  >
                    <span className="mt-1.5 h-1.5 w-1.5 flex-none rounded-full bg-teal-400" />
                    {objective}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {course.prerequisites.length > 0 && (
            <div className="mt-10">
              <h2 className="text-lg font-semibold text-foreground">
                Prerequisites
              </h2>
              <ul className="mt-4 space-y-2">
                {course.prerequisites.map((prerequisite) => (
                  <li
                    key={prerequisite}
                    className="flex items-start gap-2 text-sm text-foreground/70"
                  >
                    <span className="mt-1.5 h-1.5 w-1.5 flex-none rounded-full bg-foreground/30" />
                    {prerequisite}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {preview.length > 0 && (
            <div className="mt-10">
              <h2 className="text-lg font-semibold text-foreground">
                Free preview
              </h2>
              <div className="mt-4 divide-y divide-border overflow-hidden rounded-xl border border-border">
                {preview.map((section) => (
                  <div key={section.section} className="bg-surface">
                    <div className="flex items-center gap-2 bg-surface px-5 py-3">
                      <Layers className="h-4 w-4 text-teal-400" />
                      <span className="text-sm font-medium text-foreground">
                        {section.section}
                      </span>
                    </div>
                    <ul>
                      {section.lessons.map((lesson) => (
                        <li
                          key={lesson.id}
                          className="flex items-center justify-between gap-4 px-5 py-3 text-sm text-foreground/70"
                        >
                          <span className="flex items-center gap-2">
                            <BookOpen className="h-4 w-4 flex-none text-foreground/40" />
                            {lesson.title}
                          </span>
                          <span className="flex flex-none items-center gap-1 text-xs text-foreground/40">
                            <Clock className="h-3.5 w-3.5" />
                            {formatDuration(lesson.duration_seconds)}
                          </span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </div>
          )}

          <CourseLiveSessions courseId={course.id} sessions={liveSessions} />

          <CourseDiscussion courseId={course.id} initialPosts={discussionPosts} />

          {course.tags.length > 0 && (
            <div className="mt-10 flex flex-wrap gap-2">
              {course.tags.map((tag) => (
                <span
                  key={tag.id}
                  className="rounded-full border border-border-strong px-3 py-1 text-xs text-foreground/50"
                >
                  #{tag.name}
                </span>
              ))}
            </div>
          )}
        </div>

        <div className="lg:col-span-1">
          <div className="sticky top-24 overflow-hidden rounded-2xl border border-border bg-surface shadow-sm">
            {course.cover_image ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={course.cover_image}
                alt={course.title}
                className="aspect-video w-full object-cover"
              />
            ) : (
              <div className="flex aspect-video items-center justify-center bg-teal-500">
                <BookOpen className="h-10 w-10 text-emerald-950/80" strokeWidth={1.5} />
              </div>
            )}

            <div className="p-6">
              <p className="text-3xl font-semibold text-foreground">
                {isFree ? "Free" : `${course.currency} ${course.price_amount}`}
              </p>
              <div className="mt-6">
                <EnrollButton course={course} />
              </div>
              <ul className="mt-6 space-y-3 border-t border-border pt-6 text-sm text-foreground/60">
                <li className="flex items-center gap-2">
                  <BookOpen className="h-4 w-4 text-teal-400" />
                  Quizzes, assignments &amp; coding exercises
                </li>
                <li className="flex items-center gap-2">
                  <Layers className="h-4 w-4 text-teal-400" />
                  Certificate on completion
                </li>
                <li className="flex items-center gap-2">
                  <Globe2 className="h-4 w-4 text-teal-400" />
                  Taught in {course.language.toUpperCase()}
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
