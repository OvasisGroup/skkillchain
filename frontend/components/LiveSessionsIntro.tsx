import { CalendarClock, Radio, Users, Video } from "lucide-react";

const POINTS = [
  "Instructors schedule sessions with one-click Zoom or Google Meet integration",
  "Register in a click — the join link only unlocks in the window right before it starts",
  "Missed it? Catch the recording afterward, right from the course page",
];

export function LiveSessionsIntro() {
  return (
    <div className="grid grid-cols-1 items-center gap-12 rounded-2xl border border-border bg-surface p-8 lg:grid-cols-2 lg:p-10">
      <div className="order-2 rounded-2xl border border-border bg-background p-8 lg:order-1">
        <div className="space-y-4">
          <div className="flex items-center justify-between rounded-xl border border-border bg-surface p-5">
            <span className="flex items-center gap-2 text-sm font-medium text-foreground/70">
              <Radio className="h-4 w-4 text-emerald-400" />
              Live now
            </span>
            <span className="rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-medium text-emerald-400">
              Live Q&amp;A: Week 3
            </span>
          </div>
          <div className="flex items-center justify-between rounded-xl border border-border bg-surface p-5">
            <span className="flex items-center gap-2 text-sm font-medium text-foreground/50">
              <CalendarClock className="h-4 w-4 text-teal-400" />
              Next session
            </span>
            <span className="text-sm font-semibold text-foreground">Tomorrow, 6:00 PM</span>
          </div>
          <div className="flex items-center justify-between rounded-xl border border-border bg-surface p-5">
            <span className="flex items-center gap-2 text-sm font-medium text-foreground/50">
              <Users className="h-4 w-4 text-teal-400" />
              Registered
            </span>
            <span className="text-sm font-semibold text-foreground">86 students</span>
          </div>
        </div>
      </div>

      <div className="order-1 lg:order-2">
        <p className="text-sm font-semibold uppercase tracking-wider text-lime-400">
          Live sessions
        </p>
        <h2 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          Learn live. <span className="text-teal-400">Not just on your own.</span>
        </h2>
        <p className="mt-4 text-lg text-foreground/60">
          Join instructor-led sessions on top of self-paced lessons — ask questions in real time,
          or watch the recording later if you can&apos;t make it.
        </p>

        <ul className="mt-8 space-y-4">
          {POINTS.map((point) => (
            <li key={point} className="flex items-start gap-3">
              <Video className="mt-0.5 h-5 w-5 flex-none text-teal-400" />
              <span className="text-sm text-foreground/70">{point}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
