// Mirrors BlogHighlights' markup exactly (same wrapper classes, same 3-up
// grid) so swapping it out for the real section once the blog fetch
// resolves doesn't shift layout. Same shape as InstructorsSkeleton.
export function BlogHighlightsSkeleton() {
  return (
    <section className="mx-auto max-w-7xl px-6 py-24">
      <div className="mx-auto max-w-4xl text-center">
        <p className="text-sm font-semibold uppercase tracking-wider text-lime-400">Blog</p>
        <h2 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          From the SkillChain blog
        </h2>
        <p className="mt-4 text-lg text-foreground/60">
          News, guides, and updates from the team.
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
              <div className="h-4 w-2/3 rounded-full bg-surface-hover" />
              <div className="h-3 w-full rounded-full bg-surface-hover" />
              <div className="h-3 w-1/2 rounded-full bg-surface-hover" />
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
