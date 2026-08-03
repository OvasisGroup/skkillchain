import { AboutCta } from "@/components/about/AboutCta";
import { AboutHero } from "@/components/about/AboutHero";
import { Compliance } from "@/components/about/Compliance";
import { Curriculum } from "@/components/about/Curriculum";
import { Differentiators } from "@/components/about/Differentiators";
import { InstructorProgram } from "@/components/about/InstructorProgram";
import { MissionApproach } from "@/components/about/MissionApproach";
import { Outcomes } from "@/components/about/Outcomes";
import { Partners } from "@/components/about/Partners";

export const metadata = {
  title: "About us",
  description:
    "SkillChain is the premier platform for blockchain and AI education and course creation in Africa.",
  alternates: { canonical: "/about" },
};

export default function AboutPage() {
  return (
    <>
      <AboutHero />
      <MissionApproach />
      <Differentiators />
      <Curriculum />
      <InstructorProgram />
      <Outcomes />
      <Partners />
      <Compliance />
      <AboutCta />
    </>
  );
}
