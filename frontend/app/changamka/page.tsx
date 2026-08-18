import { BuiltForYou } from "@/components/changamka/BuiltForYou";
import { ChangamkaCta } from "@/components/changamka/ChangamkaCta";
import { ChangamkaHero } from "@/components/changamka/ChangamkaHero";
import { CurriculumPillars } from "@/components/changamka/CurriculumPillars";
import { ForInstitutions } from "@/components/changamka/ForInstitutions";
import { MindsetPillars } from "@/components/changamka/MindsetPillars";
import { WhyNow } from "@/components/changamka/WhyNow";

export const metadata = {
  title: "Changamka — AI literacy for every Kenyan student",
  description:
    "Changamka is a 20-hour, self-paced AI literacy course for Kenyan students with internationally recognized UK certification from Otermans Institute UK. Ksh 2,000. No coding required.",
  alternates: { canonical: "/changamka" },
};

export default function ChangamkaPage() {
  return (
    <>
      <ChangamkaHero />
      <WhyNow />
      <MindsetPillars />
      <BuiltForYou />
      <CurriculumPillars />
      <ForInstitutions />
      <ChangamkaCta />
    </>
  );
}
