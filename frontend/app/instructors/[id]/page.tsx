import { BookOpen, ExternalLink, Tags, UserRound } from "lucide-react";
import Link from "next/link";
import { notFound } from "next/navigation";
import { CourseCard } from "@/components/CourseCard";
import { ApiError } from "@/lib/api/client";
import { getInstructor } from "@/lib/api/instructors";
import type { InstructorDetail } from "@/lib/api/types";
import { absoluteUrl } from "@/lib/seo";
import { Reveal } from "@/components/animation/Reveal";

const SOCIAL_LINKS: { field: keyof InstructorDetail["profile"]; label: string }[] = [
  { field: "linkedin_url", label: "LinkedIn" },
  { field: "twitter_url", label: "Twitter / X" },
  { field: "github_url", label: "GitHub" },
  { field: "youtube_url", label: "YouTube" },
  { field: "website_url", label: "Website" },
];

function displayName(instructor: InstructorDetail): string {
  const name = `${instructor.profile.first_name} ${instructor.profile.last_name}`.trim();
  return name || instructor.email;
}

function courseWord(count: number): string {
  return count === 1 ? "course" : "courses";
}

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  try {
    const instructor = await getInstructor(id);
    const name = displayName(instructor);
    const canonical = `/instructors/${instructor.id}`;
    const description =
      instructor.profile.bio ||
      `${name} teaches ${instructor.published_course_count} ${courseWord(instructor.published_course_count)} on SkillChain.`;
    return {
      title: name,
      description,
      alternates: { canonical },
      openGraph: {
        type: "profile",
        url: absoluteUrl(canonical),
        title: name,
        description,
        ...(instructor.profile.avatar ? { images: [{ url: instructor.profile.avatar }] } : {}),
      },
      twitter: {
        card: "summary_large_image",
        title: name,
        description,
        ...(instructor.profile.avatar ? { images: [instructor.profile.avatar] } : {}),
      },
    };
  } catch {
    return { title: "Instructor" };
  }
}

export default async function InstructorDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  let instructor: InstructorDetail;
  try {
    instructor = await getInstructor(id);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) notFound();
    throw err;
  }

  const name = displayName(instructor);
  const socialLinks = SOCIAL_LINKS.filter(({ field }) => instructor.profile[field]);

  return (
    <div className="mx-auto max-w-7xl px-6 py-16">
      <nav className="text-sm text-foreground/40">
        <Link href="/instructors" className="hover:text-foreground">
          Instructors
        </Link>
        <span className="mx-2">/</span>
        <span className="text-foreground">{name}</span>
      </nav>

      <Reveal className="mt-8 overflow-hidden rounded-2xl border border-border bg-surface shadow-sm">
        <div className="flex flex-col items-center gap-8 p-8 text-center sm:flex-row sm:items-start sm:text-left">
          <div className="flex h-32 w-32 flex-none items-center justify-center overflow-hidden rounded-full bg-teal-400 text-4xl font-semibold text-emerald-950 ring-4 ring-teal-400/10">
            {instructor.profile.avatar ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={instructor.profile.avatar}
                alt=""
                className="h-full w-full object-cover"
              />
            ) : (
              <UserRound className="h-14 w-14" strokeWidth={1.5} />
            )}
          </div>

          <div className="min-w-0 max-w-2xl flex-1">
            <p className="text-sm font-semibold uppercase tracking-wider text-lime-400">
              Instructor
            </p>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
              {name}
            </h1>

            {instructor.profile.bio && (
              <p className="mt-3 text-base leading-7 text-foreground/60">
                {instructor.profile.bio}
              </p>
            )}

            {instructor.categories.length > 0 && (
              <div className="mt-4 flex flex-wrap justify-center gap-2 sm:justify-start">
                {instructor.categories.map((category) => (
                  <span
                    key={category.id}
                    className="rounded-full bg-surface-hover px-2.5 py-0.5 text-xs font-medium text-foreground/70"
                  >
                    {category.name}
                  </span>
                ))}
              </div>
            )}

            <div className="mt-6 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 border-t border-border pt-6 text-sm text-foreground/60 sm:justify-start">
              <span className="flex items-center gap-1.5">
                <BookOpen className="h-4 w-4 text-teal-400" />
                {instructor.published_course_count} published{" "}
                {courseWord(instructor.published_course_count)}
              </span>
              {instructor.categories.length > 0 && (
                <span className="flex items-center gap-1.5">
                  <Tags className="h-4 w-4 text-teal-400" />
                  Teaches {instructor.categories.length}{" "}
                  {instructor.categories.length === 1 ? "category" : "categories"}
                </span>
              )}
            </div>

            {socialLinks.length > 0 && (
              <div className="mt-6 flex flex-wrap justify-center gap-2 sm:justify-start">
                {socialLinks.map(({ field, label }) => (
                  <a
                    key={field}
                    href={instructor.profile[field] as string}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1.5 rounded-full border border-border-strong px-3 py-1 text-xs font-medium text-foreground/70 transition-colors hover:bg-surface-hover hover:text-foreground"
                  >
                    {label}
                    <ExternalLink className="h-3 w-3" />
                  </a>
                ))}
              </div>
            )}
          </div>
        </div>
      </Reveal>

      <div className="mt-14">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-foreground">Courses</h2>
          <span className="text-sm text-foreground/50">
            {instructor.published_course_count} published{" "}
            {courseWord(instructor.published_course_count)}
          </span>
        </div>

        {instructor.courses.length > 0 ? (
          <Reveal className="mt-4 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3" stagger={0.08}>
            {instructor.courses.map((course) => (
              <CourseCard key={course.id} course={course} />
            ))}
          </Reveal>
        ) : (
          <div className="mt-4 flex flex-col items-center rounded-2xl border border-dashed border-border-strong py-16 text-center">
            <BookOpen className="h-10 w-10 text-foreground/30" />
            <p className="mt-4 text-sm text-foreground/50">No published courses yet.</p>
          </div>
        )}
      </div>
    </div>
  );
}
