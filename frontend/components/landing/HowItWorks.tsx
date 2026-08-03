const STEPS = [
  {
    step: "01",
    title: "Create your free account",
    description: "Register with just an email and password — you're browsing in seconds.",
  },
  {
    step: "02",
    title: "Enroll and start learning",
    description:
      "Pick a course, watch lessons, join live sessions, and ask the AI tutor whenever you're stuck.",
  },
  {
    step: "03",
    title: "Get certified",
    description:
      "Finish the course and receive a certificate with a public link anyone can verify.",
  },
];

export function HowItWorks() {
  return (
    <section className="bg-surface py-24">
      <div className="mx-auto max-w-7xl px-6">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-semibold uppercase tracking-wider text-lime-400">
            Get started
          </p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            How it works
          </h2>
        </div>

        <div className="mx-auto mt-16 grid max-w-2xl grid-cols-1 gap-10 lg:max-w-none lg:grid-cols-3">
          {STEPS.map(({ step, title, description }) => (
            <div key={step} className="relative pl-16">
              <span className="absolute left-0 top-0 text-4xl font-bold text-teal-400/20">
                {step}
              </span>
              <h3 className="text-lg font-semibold text-foreground">{title}</h3>
              <p className="mt-2 text-sm leading-6 text-foreground/60">
                {description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
