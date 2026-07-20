"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, CalendarDays, GraduationCap, MapPin, SlidersHorizontal } from "lucide-react";
import { useApp } from "@/components/app-provider";
import { PipAssistant, SampleDataBanner } from "@/components/ui";
import type { InstitutionType, StudentProfile } from "@/lib/types";

const institutionTypes: Array<{ value: InstitutionType; label: string }> = [
  { value: "in-state-community-college", label: "In-state community college" },
  { value: "out-of-state-community-college", label: "Out-of-state community college" },
  { value: "in-state-four-year", label: "In-state four-year university" },
  { value: "out-of-state-four-year", label: "Out-of-state four-year university" },
  { value: "international", label: "International university" },
];

function Toggle({ on, onToggle, label, hint }: { on: boolean; onToggle: () => void; label: string; hint?: string }) {
  return (
    <button
      type="button"
      onClick={onToggle}
      aria-pressed={on}
      className={`flex w-full items-center justify-between gap-4 rounded-[var(--radius-control)] border px-4 py-3.5 text-left transition ${on ? "border-[var(--pip-mint)] bg-[var(--mint-wash)]" : "border-[var(--border)] bg-white"}`}
    >
      <span>
        <span className="block text-sm font-semibold text-[var(--ink)]">{label}</span>
        {hint && <span className="mt-0.5 block text-[12.5px] leading-[17px] text-[var(--muted-ink)]">{hint}</span>}
      </span>
      <span className={`relative h-6 w-11 shrink-0 rounded-full transition-colors duration-[160ms] ${on ? "bg-[var(--path-green)]" : "bg-[var(--border)]"}`}>
        <span className="absolute top-[3px] size-[18px] rounded-full bg-white shadow-[0_1px_3px_rgba(35,77,60,.3)] transition-all duration-[160ms]" style={{ left: on ? 23 : 3 }} />
      </span>
    </button>
  );
}

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
    <main className="mx-auto max-w-[1040px] px-5 py-10 lg:px-16 lg:py-10">
      <div className="rise max-w-[720px]">
        <h1 className="text-[32px] font-extrabold leading-[38px] text-[var(--forest)] sm:text-[42px] sm:leading-[48px]">Let’s set your planning baseline.</h1>
        <p className="mt-2.5 text-[var(--muted-ink)]">These details shape transfer pathways and which policies apply. You can change them later.</p>
      </div>

      <div className="mt-7 grid items-start gap-8 lg:grid-cols-[minmax(0,1fr)_300px]">
        <form onSubmit={handleSubmit} className="rise grid gap-5">
          <section className="card p-6">
            <h2 className="mb-4 text-[22px] font-bold leading-7 text-[var(--forest)]">Where you are now</h2>
            <div className="grid gap-4 sm:grid-cols-2">
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
              <div className="sm:col-span-2">
                <Toggle on={form.currentlyEnrolled} onToggle={() => update("currentlyEnrolled", !form.currentlyEnrolled)} label="Currently enrolled" />
              </div>
            </div>
          </section>

          <section className="card p-6">
            <h2 className="mb-4 text-[22px] font-bold leading-7 text-[var(--forest)]">What you’ve already earned</h2>
            <Toggle
              on={form.hasExamCredit}
              onToggle={() => update("hasExamCredit", !form.hasExamCredit)}
              label="I have AP, IB, CLEP, or other exam credit"
              hint="We’ll model university credit and major applicability separately."
            />
          </section>

          <section className="card p-6">
            <h2 className="mb-4 text-[22px] font-bold leading-7 text-[var(--forest)]">Where you want to go</h2>
            <div className="grid gap-4 sm:grid-cols-2">
              <label>
                <span className="field-label">Residency for your primary target</span>
                <select className="field" value={form.residency} onChange={(event) => update("residency", event.target.value as StudentProfile["residency"])}>
                  <option value="in-state">In-state resident</option>
                  <option value="out-of-state">Out-of-state resident</option>
                  <option value="international">International student</option>
                </select>
                <span className="mt-1.5 block text-[13px] leading-[18px] text-[var(--muted-ink)]">Residency can require official review — we’ll flag anything uncertain.</span>
              </label>
              <label>
                <span className="field-label">Intended transfer term</span>
                <select className="field" value={form.targetTransferTerm} onChange={(event) => update("targetTransferTerm", event.target.value)}>
                  <option>Fall 2027</option><option>Winter 2028</option><option>Spring 2028</option><option>Fall 2028</option>
                </select>
              </label>
              <label className="sm:col-span-2">
                <span className="field-label">Preferred credit load</span>
                <select className="field" value={form.preferredCreditLoad} onChange={(event) => update("preferredCreditLoad", Number(event.target.value))}>
                  <option value={10}>10 credits · part-time</option><option value={12}>12 credits</option><option value={15}>15 credits · balanced</option><option value={18}>18 credits · intensive</option>
                </select>
              </label>
            </div>
          </section>

          <div className="flex items-center justify-between">
            <button type="button" onClick={() => router.push("/")} className="secondary-button">Back</button>
            <button type="submit" className="primary-button">Continue to transcript <ArrowRight className="size-4" /></button>
          </div>
        </form>

        <aside className="rise space-y-4 lg:sticky lg:top-[84px]">
          <PipAssistant mode="bubble" alt="Pip with a note about residency">
            Residency affects tuition and some policies — I’ll never guess on the legal parts.
          </PipAssistant>
          <div className="card overflow-hidden">
            <div className="border-b border-[var(--border)] bg-[var(--cream)] p-4">
              <p className="text-[13px] font-semibold text-[var(--forest)]">{form.firstName || "Your"}’s baseline</p>
            </div>
            <div className="space-y-4 p-4">
              {[
                [GraduationCap, "Current school", form.currentInstitution || "Not set"],
                [MapPin, "Residency", form.residency.replace("-", " ")],
                [CalendarDays, "Target term", form.targetTransferTerm],
                [SlidersHorizontal, "Course load", `${form.preferredCreditLoad} credits`],
              ].map(([Icon, label, value]) => {
                const ItemIcon = Icon as typeof GraduationCap;
                return (
                  <div key={label as string} className="flex gap-3">
                    <div className="grid size-8 shrink-0 place-items-center rounded-[10px] bg-[var(--mint-wash)] text-[var(--forest)]"><ItemIcon className="size-4" /></div>
                    <div>
                      <p className="text-[11px] font-semibold uppercase tracking-wide text-[var(--muted-ink)]">{label as string}</p>
                      <p className="mt-0.5 text-sm font-medium capitalize text-[var(--ink)]">{value as string}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
          <SampleDataBanner compact />
        </aside>
      </div>
    </main>
  );
}
