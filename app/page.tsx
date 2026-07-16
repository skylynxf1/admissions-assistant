"use client";

import Link from "next/link";
import {
  ArrowRight, BriefcaseBusiness, Building2, CheckCircle2, Compass, GraduationCap,
  Landmark, Plane, Route, School, ShieldCheck, Sparkles, Split, UploadCloud,
} from "lucide-react";
import { useApp } from "@/components/app-provider";
import type { PlanningMode } from "@/lib/types";

const modes: Array<{ id: PlanningMode; title: string; description: string; icon: typeof Route; available: boolean }> = [
  { id: "transfer", title: "Transfer planning", description: "Compare schools, majors, credit policies, and the courses that keep your options open.", icon: Split, available: true },
  { id: "first-year", title: "First-year planning", description: "Build a balanced first-year path toward your academic goals.", icon: School, available: false },
  { id: "current-degree", title: "Current-school degree", description: "Map remaining requirements at your current institution.", icon: Landmark, available: false },
  { id: "graduation", title: "Plan through graduation", description: "Lay out every term and test different graduation timelines.", icon: GraduationCap, available: false },
  { id: "graduate-prereqs", title: "Graduate prerequisites", description: "Prepare coursework for future graduate programs.", icon: Building2, available: false },
  { id: "mba", title: "MBA preparation", description: "Track academic and experience milestones for an MBA.", icon: BriefcaseBusiness, available: false },
  { id: "study-abroad", title: "Study-abroad planning", description: "Evaluate programs without losing degree progress.", icon: Plane, available: false },
];

export default function HomePage() {
  const { setMode } = useApp();
  return (
    <main>
      <section className="relative overflow-hidden bg-[var(--ink)] text-white">
        <div className="absolute inset-0 opacity-20" style={{ backgroundImage: "radial-gradient(circle at 70% 10%, #66c8b7 0, transparent 30%), radial-gradient(circle at 20% 90%, #b8ef70 0, transparent 25%)" }} />
        <div className="relative mx-auto grid max-w-[1280px] gap-12 px-5 py-16 lg:grid-cols-[1.05fr_.95fr] lg:px-8 lg:py-24">
          <div className="flex flex-col justify-center">
            <div className="mb-5 inline-flex w-fit items-center gap-2 rounded-full border border-white/15 bg-white/10 px-3 py-1.5 text-xs font-semibold text-lime-200">
              <Sparkles className="size-3.5" /> Academic planning, made explorable
            </div>
            <h1 className="max-w-3xl text-4xl font-semibold leading-[1.02] tracking-[-0.055em] sm:text-5xl lg:text-[64px]">
              Every path, mapped before you commit.
            </h1>
            <p className="mt-6 max-w-2xl text-base leading-7 text-slate-300 sm:text-lg">
              Upload your academic record, compare transfer paths, and see which courses preserve the most school and major options—without pretending uncertainty doesn’t exist.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/onboarding" onClick={() => setMode("transfer")} className="inline-flex min-h-12 items-center gap-2 rounded-xl bg-[var(--lime)] px-5 font-semibold text-[var(--ink)] transition hover:-translate-y-0.5 hover:bg-lime-300">
                Start transfer plan <ArrowRight className="size-4" />
              </Link>
              <a href="#modes" className="inline-flex min-h-12 items-center rounded-xl border border-white/20 px-5 font-semibold text-white hover:bg-white/10">Explore planning modes</a>
            </div>
            <div className="mt-10 flex flex-wrap gap-x-6 gap-y-3 text-xs text-slate-400">
              <span className="flex items-center gap-1.5"><ShieldCheck className="size-4 text-teal-300" /> Transparent confidence</span>
              <span className="flex items-center gap-1.5"><Compass className="size-4 text-teal-300" /> Multi-path simulation</span>
              <span className="flex items-center gap-1.5"><UploadCloud className="size-4 text-teal-300" /> Editable transcript review</span>
            </div>
          </div>

          <div className="relative mx-auto w-full max-w-xl lg:mx-0">
            <div className="absolute -inset-4 rounded-[32px] bg-gradient-to-br from-teal-400/20 to-lime-300/10 blur-2xl" />
            <div className="relative rounded-[28px] border border-white/15 bg-white/[0.08] p-4 shadow-2xl backdrop-blur-xl sm:p-6">
              <div className="flex items-center justify-between border-b border-white/10 pb-4">
                <div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-teal-200">Sample scenario</p><p className="mt-1 font-semibold">Alex’s transfer plan</p></div>
                <span className="rounded-full bg-lime-300/15 px-2.5 py-1 text-xs font-semibold text-lime-200">3 programs</span>
              </div>
              <div className="grid grid-cols-3 gap-3 py-5">
                {[['45','earned'],['48.5','transferable'],['3','paths']].map(([value,label]) => <div key={label} className="rounded-2xl bg-white/[0.07] p-3"><div className="text-2xl font-semibold tracking-tight">{value}</div><div className="mt-0.5 text-[11px] text-slate-400">{label}</div></div>)}
              </div>
              <div className="space-y-3">
                {[
                  ["UW · Informatics", "Nearly ready", "76%"],
                  ["UW · Computer Science", "Confirm 1 item", "64%"],
                  ["UC Berkeley · Data Science", "Credit gap", "52%"],
                ].map(([program, status, width], index) => (
                  <div key={program} className="rounded-2xl bg-white p-4 text-slate-900">
                    <div className="flex items-start justify-between gap-3"><div><p className="text-sm font-semibold">{program}</p><p className={`mt-1 text-xs ${index === 2 ? "text-amber-700" : "text-slate-500"}`}>{status}</p></div><span className="text-sm font-semibold">{width}</span></div>
                    <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-teal-500" style={{ width }} /></div>
                  </div>
                ))}
              </div>
              <div className="mt-4 flex items-center gap-3 rounded-2xl border border-lime-200/20 bg-lime-300/10 p-4">
                <div className="grid size-9 shrink-0 place-items-center rounded-xl bg-lime-300 text-[var(--ink)]"><Route className="size-4" /></div>
                <div><p className="text-sm font-semibold">Best next move</p><p className="mt-0.5 text-xs text-slate-300">MATH& 146 keeps all 3 selected paths open.</p></div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="modes" className="mx-auto max-w-[1280px] px-5 py-16 lg:px-8 lg:py-20">
        <div className="max-w-2xl">
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-teal-700">Choose your planning mode</p>
          <h2 className="mt-3 text-3xl font-semibold tracking-[-0.04em] text-[var(--ink)] sm:text-4xl">Start with where you’re headed.</h2>
          <p className="mt-3 text-slate-600">Transfer Planning is fully interactive in this prototype. The broader academic planning system is represented for what comes next.</p>
        </div>
        <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {modes.map((mode) => {
            const Icon = mode.icon;
            const content = (
              <div className={`group relative h-full rounded-2xl border p-5 transition ${mode.available ? "border-teal-200 bg-white shadow-sm hover:-translate-y-1 hover:border-teal-400 hover:shadow-xl hover:shadow-teal-950/5" : "border-slate-200 bg-white/60"}`}>
                <div className="flex items-start justify-between"><div className={`grid size-11 place-items-center rounded-xl ${mode.available ? "bg-teal-50 text-teal-700" : "bg-slate-100 text-slate-400"}`}><Icon className="size-5" /></div>{mode.available ? <span className="rounded-full bg-lime-100 px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider text-lime-800">Ready</span> : <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider text-slate-500">Coming soon</span>}</div>
                <h3 className="mt-5 text-lg font-semibold tracking-tight text-slate-900">{mode.title}</h3>
                <p className="mt-2 text-sm leading-6 text-slate-500">{mode.description}</p>
                {mode.available && <span className="mt-5 flex items-center gap-1.5 text-sm font-semibold text-teal-700">Build this plan <ArrowRight className="size-4 transition group-hover:translate-x-1" /></span>}
              </div>
            );
            return mode.available ? <Link key={mode.id} href="/onboarding" onClick={() => setMode(mode.id)}>{content}</Link> : <div key={mode.id}>{content}</div>;
          })}
        </div>
        <div className="mt-12 grid gap-4 rounded-3xl bg-white p-6 ring-1 ring-slate-200 sm:grid-cols-3 sm:p-8">
          {[
            [CheckCircle2, "Edit everything", "Review every extracted course, credit, grade, and confidence level."],
            [Split, "Keep options open", "See which courses support the greatest number of schools and majors."],
            [ShieldCheck, "Know what’s uncertain", "Draft an exact question for admissions when a policy isn’t clear."],
          ].map(([Icon, title, text]) => {
            const FeatureIcon = Icon as typeof CheckCircle2;
            return <div key={title as string} className="flex gap-3"><FeatureIcon className="mt-0.5 size-5 shrink-0 text-teal-600" /><div><h3 className="text-sm font-semibold text-slate-900">{title as string}</h3><p className="mt-1 text-sm leading-5 text-slate-500">{text as string}</p></div></div>;
          })}
        </div>
      </section>
    </main>
  );
}
