export const authInputClass =
  "mt-1.5 block w-full rounded-lg border border-border-strong bg-surface px-3.5 py-2.5 text-sm text-foreground placeholder:text-foreground/30 shadow-sm focus:border-teal-400 focus:outline-none focus:ring-1 focus:ring-teal-400";

export const authLabelClass = "block text-sm font-medium text-foreground/70";

export function AuthDivider({ label }: { label: string }) {
  return (
    <div className="my-6 flex items-center gap-3">
      <div className="h-px flex-1 bg-border" />
      <span className="text-xs text-foreground/40">{label}</span>
      <div className="h-px flex-1 bg-border" />
    </div>
  );
}

export function AuthCard({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="relative flex min-h-[calc(100vh-4rem)] items-center justify-center overflow-hidden px-6 py-16">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 -top-40 -z-10 transform-gpu blur-3xl"
      >
        <div className="mx-auto h-[30rem] w-[60rem] bg-teal-400/15 [clip-path:polygon(74%_44%,100%_61%,97%_26%,85%_0%,80%_2%,72%_32%,60%_62%,32%_35%,2%_46%,0%_68%,32%_100%,60%_75%)]" />
      </div>

      <div className="w-full max-w-md">
        <div className="rounded-2xl border border-border bg-surface p-8 shadow-xl shadow-black/30">
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            {title}
          </h1>
          <p className="mt-2 text-sm text-foreground/50">{subtitle}</p>
          <div className="mt-8">{children}</div>
        </div>
      </div>
    </div>
  );
}
