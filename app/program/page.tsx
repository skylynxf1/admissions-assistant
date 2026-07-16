"use client";

import { useRouter } from "next/navigation";
import { ArrowRight, BookOpenCheck, Check, Code2, GraduationCap, MapPin, Scale, Sparkles } from "lucide-react";
import { useApp } from "@/components/app-provider";
import { getSchool } from "@/data/sample-policies";

export default function ProgramPage() {
  const router = useRouter();
  const { targets, setTargets, prioritySchoolId } = useApp();
  const school = getSchool(prioritySchoolId);
  const target = targets.find((item) => item.schoolId === prioritySchoolId);
  const selectedMajorIds = target?.majorIds ?? [];

  if (!school || !target) {
    return <main className="mx-auto max-w-xl px-5 py-20 text-center"><h1 className="text-2xl font-semibold text-slate-900">Choose a priority school first.</h1><button onClick={() => router.push("/targets")} className="primary-button mt-5">Back to schools</button></main>;
  }

  const toggleMajor = (majorId: string) => {
    setTargets(targets.map((item) => item.schoolId === prioritySchoolId
      ? { ...item, majorIds: item.majorIds.includes(majorId) ? item.majorIds.filter((id) => id !== majorId) : [...item.majorIds, majorId] }
      : item));
  };

  const outline = [
    { Icon: GraduationCap, title: "Transfer standing", text: `${school.minimumTransferCredits} sample minimum credits; ${school.preferredCreditRange[0]}–${school.preferredCreditRange[1]} is the preferred range.` },
    { Icon: BookOpenCheck, title: "Writing", text: "One college composition course should be completed before transfer." },
    { Icon: Scale, title: "Math foundation", text: "Calculus and statistics keep the widest set of selected program paths open." },
    { Icon: Code2, title: "Major preparation", text: "Programming I → Programming II → Data Structures is the main sample prerequisite chain." },
  ];

  return (
    <main className="mx-auto max-w-5xl px-5 py-10 lg:px-8 lg:py-12">
      <section className="overflow-hidden rounded-3xl bg-[var(--ink)] text-white shadow-xl shadow-slate-900/10">
        <div className="grid gap-8 p-6 sm:p-8 lg:grid-cols-[1fr_320px] lg:p-10">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.16em] text-lime-200">Your priority school</p>
            <h1 className="mt-3 text-3xl font-semibold tracking-[-0.045em] sm:text-4xl">{school.name}</h1>
            <p className="mt-3 flex items-center gap-1.5 text-sm text-slate-300"><MapPin className="size-4" /> {school.location}</p>
            <div className="mt-7"><h2 className="text-lg font-semibold">What are you interested in studying?</h2><p className="mt-1 text-sm text-slate-300">Choose one or more majors. You can add more later from the planner.</p></div>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              {school.majors.map((major) => {
                const selected = selectedMajorIds.includes(major.id);
                return <button key={major.id} onClick={() => toggleMajor(major.id)} className={`flex items-start gap-3 rounded-2xl border p-4 text-left transition ${selected ? "border-lime-300 bg-white text-slate-900" : "border-white/15 bg-white/[0.06] text-white hover:bg-white/10"}`}><span className={`mt-0.5 grid size-5 shrink-0 place-items-center rounded-full border ${selected ? "border-teal-600 bg-teal-600 text-white" : "border-white/30 text-transparent"}`}><Check className="size-3" /></span><span><span className="block text-sm font-semibold">{major.name}</span><span className={`mt-1 block text-xs ${selected ? "text-slate-500" : "text-slate-400"}`}>{major.college}</span></span></button>;
              })}
            </div>
          </div>
          <aside className="rounded-2xl bg-white p-5 text-slate-900">
            <div className="flex items-center gap-2"><Sparkles className="size-4 text-teal-600" /><h2 className="font-semibold">At a glance</h2></div>
            <p className="mt-2 text-xs leading-5 text-slate-500">A short sample outline before we personalize it with your transcript.</p>
            <div className="mt-4 space-y-3">
              {outline.map(({ Icon, title, text }) => <div key={title} className="flex gap-3 rounded-xl bg-slate-50 p-3"><div className="grid size-8 shrink-0 place-items-center rounded-lg bg-white text-teal-700 shadow-sm"><Icon className="size-4" /></div><div><p className="text-xs font-semibold text-slate-900">{title}</p><p className="mt-1 text-[11px] leading-4 text-slate-500">{text}</p></div></div>)}
            </div>
            <p className="mt-4 text-[10px] leading-4 text-amber-700">Sample data only. Policy details are not yet verified from a live scrape.</p>
          </aside>
        </div>
      </section>

      <div className="mt-6 flex flex-col gap-4 rounded-2xl border border-teal-200 bg-teal-50 p-5 sm:flex-row sm:items-center sm:justify-between">
        <div><p className="font-semibold text-teal-950">Ready to apply this to your record?</p><p className="mt-1 text-sm text-teal-700">We’ll turn the outline into an editable quarter-by-quarter plan.</p></div>
        <button disabled={selectedMajorIds.length === 0} onClick={() => router.push("/dashboard")} className="primary-button shrink-0">How does this work for me? <ArrowRight className="size-4" /></button>
      </div>
    </main>
  );
}
