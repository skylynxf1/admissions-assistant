"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, BookOpenCheck, CalendarDays, GraduationCap, MapPin, SlidersHorizontal } from "lucide-react";
import { useApp } from "@/components/app-provider";
import { SampleDataBanner } from "@/components/ui";
import type { InstitutionType, StudentProfile } from "@/lib/types";

const institutionTypes: Array<{ value: InstitutionType; label: string }> = [
  { value: "in-state-community-college", label: "In-state community college" },
  { value: "out-of-state-community-college", label: "Out-of-state community college" },
  { value: "in-state-four-year", label: "In-state four-year university" },
  { value: "out-of-state-four-year", label: "Out-of-state four-year university" },
  { value: "international", label: "International university" },
];

export default function OnboardingPage() {
  const router = useRouter();
  const { profile, setProfile } = useApp();
  const [form, setForm] = useState<StudentProfile>(profile);

  const update = <K extends keyof StudentProfile>(key: K, value: StudentProfile[K]) => {
    setForm((current) => ({ ...current, [key]: value }));
  };

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    setProfile(form);
    router.push("/transcript");
  };

  return (
    <main className="mx-auto max-w-5xl px-5 py-10 lg:px-8 lg:py-14">
      <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_300px]">
        <section>
          <div className="mb-8">
            <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-teal-50 px-3 py-1 text-xs font-semibold text-teal-700">
              <BookOpenCheck className="size-3.5" /> Transfer planning
            </div>
            <h1 className="text-3xl font-semibold tracking-[-0.045em] text-[var(--ink)] sm:text-4xl">Let’s set your planning baseline.</h1>
            <p className="mt-3 max-w-2xl text-slate-600">These details affect transfer pathways, credit assumptions, and which policies the simulator applies. You can change them later.</p>
          </div>

          <form onSubmit={handleSubmit} className="card p-5 sm:p-7">
            <div className="grid gap-5 sm:grid-cols-2">
              <label>
                <span className="field-label">Preferred name</span>
                <input className="field" value={form.firstName} onChange={(event) => update("firstName", event.target.value)} placeholder="Alex" required />
              </label>
              <label>
                <span className="field-label">Current institution</span>
                <input className="field" value={form.currentInstitution} onChange={(event) => update("currentInstitution", event.target.value)} placeholder="Bellevue College" required />
              </label>
              <label className="sm:col-span-2">
                <span className="field-label">Current-school type</span>
                <select className="field" value={form.institutionType} onChange={(event) => update("institutionType", event.target.value as InstitutionType)}>
                  {institutionTypes.map((type) => <option key={type.value} value={type.value}>{type.label}</option>)}
                </select>
              </label>
              <label>
                <span className="field-label">Residency for your primary target</span>
                <select className="field" value={form.residency} onChange={(event) => update("residency", event.target.value as StudentProfile["residency"])}>
                  <option value="in-state">In-state resident</option>
                  <option value="out-of-state">Out-of-state resident</option>
                  <option value="international">International student</option>
                </select>
              </label>
              <label>
                <span className="field-label">Intended transfer term</span>
                <select className="field" value={form.targetTransferTerm} onChange={(event) => update("targetTransferTerm", event.target.value)}>
                  <option>Fall 2027</option><option>Winter 2028</option><option>Spring 2028</option><option>Fall 2028</option>
                </select>
              </label>
              <label>
                <span className="field-label">Preferred credit load</span>
                <select className="field" value={form.preferredCreditLoad} onChange={(event) => update("preferredCreditLoad", Number(event.target.value))}>
                  <option value={10}>10 credits · part-time</option><option value={12}>12 credits</option><option value={15}>15 credits · balanced</option><option value={18}>18 credits · intensive</option>
                </select>
              </label>
              <div>
                <span className="field-label">Academic status</span>
                <button type="button" onClick={() => update("currentlyEnrolled", !form.currentlyEnrolled)} className={`flex w-full items-center justify-between rounded-xl border px-4 py-3 text-left text-sm transition ${form.currentlyEnrolled ? "border-teal-300 bg-teal-50 text-teal-900" : "border-slate-200 bg-white text-slate-600"}`}>
                  <span>Currently enrolled</span><span className={`relative h-5 w-9 rounded-full transition ${form.currentlyEnrolled ? "bg-teal-600" : "bg-slate-300"}`}><span className={`absolute top-0.5 size-4 rounded-full bg-white shadow-sm transition ${form.currentlyEnrolled ? "left-[18px]" : "left-0.5"}`} /></span>
                </button>
              </div>
              <div className="sm:col-span-2 rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <button type="button" onClick={() => update("hasExamCredit", !form.hasExamCredit)} className="flex w-full items-center justify-between gap-4 text-left">
                  <div><p className="text-sm font-semibold text-slate-900">I have AP, IB, CLEP, or other exam credit</p><p className="mt-1 text-xs text-slate-500">We’ll model university credit and major applicability separately.</p></div>
                  <span className={`relative h-6 w-11 shrink-0 rounded-full transition ${form.hasExamCredit ? "bg-teal-600" : "bg-slate-300"}`}><span className={`absolute top-1 size-4 rounded-full bg-white shadow-sm transition ${form.hasExamCredit ? "left-6" : "left-1"}`} /></span>
                </button>
              </div>
            </div>
            <div className="mt-7 flex items-center justify-between border-t border-slate-100 pt-5">
              <button type="button" onClick={() => router.push("/")} className="secondary-button">Back</button>
              <button type="submit" className="primary-button">Continue to transcript <ArrowRight className="size-4" /></button>
            </div>
          </form>
        </section>

        <aside className="space-y-4 lg:pt-28">
          <div className="card overflow-hidden">
            <div className="bg-[var(--ink)] p-5 text-white"><p className="text-xs font-semibold uppercase tracking-[0.14em] text-teal-200">Scenario preview</p><p className="mt-2 text-lg font-semibold">{form.firstName || "Your"}’s baseline</p></div>
            <div className="space-y-4 p-5">
              {[
                [GraduationCap, "Current school", form.currentInstitution || "Not set"],
                [MapPin, "Residency", form.residency.replace("-", " ")],
                [CalendarDays, "Target term", form.targetTransferTerm],
                [SlidersHorizontal, "Course load", `${form.preferredCreditLoad} credits`],
              ].map(([Icon, label, value]) => {
                const ItemIcon = Icon as typeof GraduationCap;
                return <div key={label as string} className="flex gap-3"><div className="grid size-8 shrink-0 place-items-center rounded-lg bg-slate-100 text-slate-500"><ItemIcon className="size-4" /></div><div><p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">{label as string}</p><p className="mt-0.5 text-sm font-medium capitalize text-slate-800">{value as string}</p></div></div>;
              })}
            </div>
          </div>
          <SampleDataBanner compact />
        </aside>
      </div>
    </main>
  );
}
