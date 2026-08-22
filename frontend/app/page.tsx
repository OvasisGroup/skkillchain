import { Suspense } from "react";
import { BlogHighlights } from "@/components/landing/BlogHighlights";
import { BlogHighlightsSkeleton } from "@/components/landing/BlogHighlightsSkeleton";
import { CapabilityStrip } from "@/components/landing/CapabilityStrip";
import { Courses } from "@/components/landing/Courses";
import { CoursesSkeleton } from "@/components/landing/CoursesSkeleton";
import { CtaBanner } from "@/components/landing/CtaBanner";
import { Features } from "@/components/landing/Features";
import { ForInstructors } from "@/components/landing/ForInstructors";
import { Hero } from "@/components/landing/Hero";
import { HowItWorks } from "@/components/landing/HowItWorks";
import { Instructors } from "@/components/landing/Instructors";
import { InstructorsSkeleton } from "@/components/landing/InstructorsSkeleton";

export default function Home() {
  return (
    <>
      <Hero />
      <CapabilityStrip />
      <Features />
      <Suspense fallback={<CoursesSkeleton />}>
        <Courses />
      </Suspense>
      <Suspense fallback={<InstructorsSkeleton />}>
        <Instructors />
      </Suspense>
      <HowItWorks />
      <ForInstructors />
      <Suspense fallback={<BlogHighlightsSkeleton />}>
        <BlogHighlights />
      </Suspense>
      <CtaBanner />
    </>
  );
}
