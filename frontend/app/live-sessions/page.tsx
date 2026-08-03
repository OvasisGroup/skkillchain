import { AlertTriangle, Radio } from "lucide-react";
import { LiveSessionsBrowser, type CourseLiveSessionEntry } from "@/components/LiveSessionsBrowser";
import { LiveSessionsIntro } from "@/components/LiveSessionsIntro";
import { listCourses } from "@/lib/api/courses";
import { listCourseLiveSessions } from "@/lib/api/liveSessions";

export const metadata = {
  title: "Live sessions",
  description:
    "Join live, instructor-led sessions on SkillChain — real-time Q&A, coding walkthroughs, and interactive lessons across our blockchain and AI courses.",
  alternates: { canonical: "/live-sessions" },
};

export default async function LiveSessionsPage() {
  let entries: CourseLiveSessionEntry[] = [];
  let loadError: string | null = null;

  try {
    const { results: courses } = await listCourses();
    const perCourseSessions = await Promise.all(
      courses.map((course) =>
        listCourseLiveSessions(course.id).catch(() => [])
      )
    );
    entries = courses.flatMap((course, index) =>
      perCourseSessions[index]
        .filter((session) => session.status !== "canceled")
        .map((session) => ({ session, course }))
    );
  } catch {
    loadError =
      "We couldn't reach the live sessions schedule right now. Make sure the SkillChain API is running.";
  }

  return (
    <div className="mx-auto max-w-7xl px-6 py-16">
      <div className="max-w-2xl">
        <p className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-lime-400">
          Live sessions
          <Radio className="h-4 w-4" />
        </p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          Learn live, across every course
        </h1>
        <p className="mt-3 text-lg text-foreground/60">
          Register for instructor-led sessions running over Zoom or Google Meet, or catch up on
          the recording afterward.
        </p>
      </div>

      <div className="mt-12">
        <LiveSessionsIntro />
      </div>

      {loadError && (
        <div className="mt-10 flex items-start gap-3 rounded-xl border border-amber-500/20 bg-amber-500/10 p-4 text-sm text-amber-400">
          <AlertTriangle className="mt-0.5 h-5 w-5 flex-none" />
          <span>{loadError}</span>
        </div>
      )}

      {!loadError && <LiveSessionsBrowser entries={entries} />}
    </div>
  );
}
