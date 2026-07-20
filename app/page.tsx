"use client";

/* eslint-disable @next/next/no-img-element */
import Link from "next/link";
import {
  ArrowRight, BriefcaseBusiness, Building2, CheckCircle2, GraduationCap,
  Landmark, Plane, Route, School, ShieldCheck, Split,
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

const outcomes = [
  ["Understand transfer credit", "See what transfers — and what counts toward each major, separately."],
  ["Compare paths", "Line up several schools and majors and find the overlap."],
  ["Plan next courses", "Pick courses that keep the most options open."],
];

export default function HomePage() {
  const { setMode } = useApp();
  return (
    <main>
      <section className="pathly-grid">
        <div className="mx-auto grid max-w-[1200px] items-center gap-12 px-5 py-14 lg:grid-cols-[1.1fr_.9fr] lg:px-16 lg:py-[72px]">
          <div className="rise">
            <span className="inline-flex items-center gap-2 rounded-full border border-[var(--pip-mint)] bg-[var(--mint-wash)] px-3.5 py-1.5 text-[13px] font-semibold text-[var(--forest)]">
              ✦ For transfer students
            </span>
            <h1 className="mt-[18px] max-w-[560px] text-[42px] font-extrabold leading-[48px] text-[var(--forest)] lg:text-[56px] lg:leading-[60px]" style={{ textWrap: "pretty" }}>
              Let’s map your clearest path.
            </h1>
            <p className="mt-[18px] max-w-[520px] text-lg leading-[29px] text-[var(--muted-ink)]">
              Upload your record, compare schools and majors, and see which courses keep the most options open — without pretending uncertainty doesn’t exist.
            </p>
            <div className="mt-7 flex flex-wrap gap-3">
              <Link href="/onboarding" onClick={() => setMode("transfer")} className="cta-button min-h-[52px]">
                Start my transfer plan
              </Link>
              <a href="#modes" className="secondary-button min-h-[52px]">How it works</a>
            </div>
            <div className="mt-11 grid gap-3 sm:grid-cols-3">
              {outcomes.map(([title, description]) => (
                <div key={title} className="rounded-[var(--radius-card)] border border-[var(--border)] bg-white p-4">
                  <div className="text-[15px] font-bold leading-5 text-[var(--forest)]" style={{ fontFamily: "var(--font-heading)" }}>{title}</div>
                  <p className="mt-1.5 text-[13px] leading-[19px] text-[var(--muted-ink)]">{description}</p>
                </div>
              ))}
            </div>
          </div>
          <div className="relative hidden place-items-center lg:grid">
            <div className="absolute -inset-10" style={{ background: "var(--gradient-hero-glow)" }} />
            <img
              src="/pathly/reactions/pip-reaction-00.png"
              alt="Pip, your transfer guide, waving hello"
              width={330}
              className="relative"
              style={{ animation: "rise var(--dur-mascot) var(--ease-brand) both 120ms" }}
            />
          </div>
        </div>
      </section>

      <section id="modes" className="mx-auto max-w-[1200px] px-5 py-16 lg:px-16 lg:py-20">
        <div className="max-w-2xl">
          <p className="text-[13px] font-semibold text-[var(--path-green)]">Choose your planning mode</p>
          <h2 className="mt-3 text-[32px] font-bold leading-[38px] text-[var(--forest)]">Start with where you’re headed.</h2>
          <p className="mt-3 text-[var(--muted-ink)]">Transfer planning is fully interactive in this prototype. The broader academic planning system is represented for what comes next.</p>
        </div>
        <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {modes.map((mode) => {
            const Icon = mode.icon;
            const content = (
              <div className={`group relative h-full rounded-[var(--radius-card)] border bg-white p-5 transition-all duration-[160ms] ${mode.available ? "border-[var(--border)] shadow-[var(--shadow-card)] hover:-translate-y-0.5 hover:border-[var(--pip-mint)] hover:shadow-[var(--shadow-hover)]" : "border-[var(--border)] bg-white/60"}`}>
                <div className="flex items-start justify-between">
                  <div className={`grid size-11 place-items-center rounded-[var(--radius-control)] ${mode.available ? "bg-[var(--mint-wash)] text-[var(--forest)]" : "bg-[var(--paper)] text-[var(--muted-ink)]"}`}><Icon className="size-5" /></div>
                  {mode.available
                    ? <span className="rounded-full border border-[var(--pip-mint)] bg-[var(--mint-wash)] px-2.5 py-1 text-[11px] font-semibold text-[var(--forest)]">Ready now</span>
                    : <span className="rounded-full border border-[var(--border)] bg-[var(--paper)] px-2.5 py-1 text-[11px] font-semibold text-[var(--muted-ink)]">Coming soon</span>}
                </div>
                <h3 className="mt-5 text-[17px] font-bold text-[var(--forest)]">{mode.title}</h3>
                <p className="mt-2 text-sm leading-6 text-[var(--muted-ink)]">{mode.description}</p>
                {mode.available && <span className="mt-5 flex items-center gap-1.5 text-sm font-bold text-[var(--path-green)]">Build this plan <ArrowRight className="size-4 transition group-hover:translate-x-1" /></span>}
              </div>
            );
            return mode.available ? <Link key={mode.id} href="/onboarding" onClick={() => setMode(mode.id)}>{content}</Link> : <div key={mode.id}>{content}</div>;
          })}
        </div>
        <div className="mt-12 grid gap-4 rounded-[var(--radius-card)] border border-[var(--border)] bg-white p-6 shadow-[var(--shadow-card)] sm:grid-cols-3 sm:p-8">
          {[
            [CheckCircle2, "Edit everything", "Review every extracted course, credit, grade, and confidence level."],
            [Split, "Keep options open", "See which courses support the greatest number of schools and majors."],
            [ShieldCheck, "Know what’s uncertain", "Draft an exact question for admissions when a policy isn’t clear."],
          ].map(([Icon, title, text]) => {
            const FeatureIcon = Icon as typeof CheckCircle2;
            return (
              <div key={title as string} className="flex gap-3">
                <FeatureIcon className="mt-0.5 size-5 shrink-0 text-[var(--path-green)]" />
                <div>
                  <h3 className="text-sm font-bold text-[var(--forest)]">{title as string}</h3>
                  <p className="mt-1 text-sm leading-5 text-[var(--muted-ink)]">{text as string}</p>
                </div>
              </div>
            );
          })}
        </div>
      </section>
    </main>
  );
}
