import { BookX } from "lucide-react";
import Link from "next/link";

export default function CourseNotFound() {
  return (
    <div className="mx-auto max-w-2xl px-6 py-32 text-center">
      <BookX className="mx-auto h-10 w-10 text-foreground/30" />
      <h1 className="mt-6 text-2xl font-semibold text-foreground">
        Course not found
      </h1>
      <p className="mt-3 text-sm text-foreground/50">
        This course doesn&apos;t exist, or hasn&apos;t been published yet.
      </p>
      <Link
        href="/courses"
        className="mt-8 inline-flex items-center gap-2 rounded-full bg-teal-400 px-6 py-3 text-sm font-semibold text-emerald-950 transition-opacity hover:opacity-90"
      >
        Browse all courses
      </Link>
    </div>
  );
}
