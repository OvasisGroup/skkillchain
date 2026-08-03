// Mirrors Courses' markup exactly (same wrapper classes, same 3-up grid) so
// swapping it out for the real section once the course fetch resolves
// doesn't shift layout.
export function CoursesSkeleton() {
  return (
    <section className="bg-surface py-24">
      <div className="mx-auto max-w-7xl px-6">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-semibold uppercase tracking-wider text-lime-400">
            Catalog
          </p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            Courses to get you building
          </h2>
          <p className="mt-4 text-lg text-foreground/60">
            A sample of what&apos;s live right now — browse the full catalog for everything else.
          </p>
        </div>

        <div className="mx-auto mt-16 grid max-w-2xl grid-cols-1 gap-6 sm:grid-cols-2 lg:max-w-none lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div
              key={i}
              className="animate-pulse overflow-hidden rounded-2xl border border-border bg-surface"
            >
              <div className="aspect-video bg-surface-hover" />
              <div className="space-y-3 p-5">
                <div className="h-3 w-1/3 rounded-full bg-surface-hover" />
                <div className="h-4 w-3/4 rounded-full bg-surface-hover" />
                <div className="h-3 w-full rounded-full bg-surface-hover" />
                <div className="h-3 w-2/3 rounded-full bg-surface-hover" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
