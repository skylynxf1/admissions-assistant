"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Building2, Check, ChevronDown, MapPin, Plus, ShieldAlert, Trash2 } from "lucide-react";
import { useApp } from "@/components/app-provider";
import { SampleDataBanner } from "@/components/ui";
import { getMajor, getSchool, schoolCatalog } from "@/data/sample-policies";

export default function TargetsPage() {
  const router = useRouter();
  const { targets, setTargets } = useApp();
  const [schoolToAdd, setSchoolToAdd] = useState(schoolCatalog.find((school) => !targets.some((target) => target.schoolId === school.id))?.id ?? "");

  const toggleMajor = (schoolId: string, majorId: string) => {
    setTargets(targets.map((target) => target.schoolId === schoolId
      ? { ...target, majorIds: target.majorIds.includes(majorId) ? target.majorIds.filter((id) => id !== majorId) : [...target.majorIds, majorId] }
      : target));
  };

  const addSchool = () => {
    const school = getSchool(schoolToAdd);
    if (!school || targets.some((target) => target.schoolId === school.id)) return;
    const next = [...targets, { schoolId: school.id, majorIds: school.majors.slice(0, 1).map((major) => major.id) }];
    setTargets(next);
    setSchoolToAdd(schoolCatalog.find((candidate) => !next.some((target) => target.schoolId === candidate.id))?.id ?? "");
  };

  const selectedPrograms = targets.reduce((sum, target) => sum + target.majorIds.length, 0);
  const canContinue = targets.length > 0 && selectedPrograms > 0 && targets.every((target) => target.majorIds.length > 0);

  return (
    <main className="mx-auto max-w-6xl px-5 py-10 lg:px-8 lg:py-12">
      <div className="max-w-3xl"><p className="text-xs font-bold uppercase tracking-[0.16em] text-teal-700">Destination paths</p><h1 className="mt-2 text-3xl font-semibold tracking-[-0.045em] text-[var(--ink)]">Compare every school and major you’re considering.</h1><p className="mt-3 text-slate-600">Add multiple targets. The recommendation engine will optimize for courses that keep the greatest number of these paths open.</p></div>

      <div className="mt-8 grid gap-6 lg:grid-cols-[minmax(0,1fr)_290px]">
        <section className="space-y-4">
          {targets.map((target, targetIndex) => {
            const school = getSchool(target.schoolId);
            if (!school) return null;
            return (
              <article key={target.schoolId} className="card overflow-hidden">
                <div className="flex items-start justify-between gap-4 border-b border-slate-100 px-5 py-4 sm:px-6">
                  <div className="flex gap-3"><div className="grid size-11 shrink-0 place-items-center rounded-xl text-white" style={{ backgroundColor: school.color }}><Building2 className="size-5" /></div><div><div className="flex flex-wrap items-center gap-2"><h2 className="font-semibold text-slate-900">{school.name}</h2><span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-slate-500">Target {targetIndex + 1}</span></div><p className="mt-1 flex items-center gap-1 text-xs text-slate-500"><MapPin className="size-3" />{school.location}</p></div></div>
                  <button onClick={() => setTargets(targets.filter((item) => item.schoolId !== target.schoolId))} aria-label={`Remove ${school.name}`} className="rounded-lg p-2 text-slate-400 hover:bg-rose-50 hover:text-rose-600"><Trash2 className="size-4" /></button>
                </div>
                <div className="p-5 sm:p-6">
                  <div className="flex items-center justify-between"><div><h3 className="text-sm font-semibold text-slate-900">Select majors</h3><p className="mt-1 text-xs text-slate-500">Choose one or more pathways at this school.</p></div><span className="text-xs font-medium text-slate-400">{target.majorIds.length} selected</span></div>
                  <div className="mt-4 grid gap-3 sm:grid-cols-2">
                    {school.majors.map((major) => {
                      const selected = target.majorIds.includes(major.id);
                      return (
                        <button key={major.id} onClick={() => toggleMajor(school.id, major.id)} className={`relative rounded-xl border p-4 text-left transition ${selected ? "border-teal-400 bg-teal-50/70 ring-2 ring-teal-100" : "border-slate-200 bg-white hover:border-slate-300"}`}>
                          <div className="flex items-start justify-between gap-3"><div><p className="text-sm font-semibold text-slate-900">{major.name}</p><p className="mt-1 line-clamp-1 text-xs text-slate-500">{major.college}</p></div><span className={`grid size-5 shrink-0 place-items-center rounded-full border ${selected ? "border-teal-600 bg-teal-600 text-white" : "border-slate-300 text-transparent"}`}><Check className="size-3" /></span></div>
                          <span className={`mt-3 inline-flex rounded-md px-2 py-1 text-[10px] font-semibold capitalize ${major.admissionType === "capacity-constrained" ? "bg-rose-50 text-rose-700" : "bg-amber-50 text-amber-700"}`}>{major.admissionType.replace("-", " ")}</span>
                        </button>
                      );
                    })}
                  </div>
                  {target.majorIds.length === 0 && <p className="mt-3 flex items-center gap-1.5 text-xs font-medium text-rose-600"><ShieldAlert className="size-3.5" /> Select at least one major for this school.</p>}
                  <div className="mt-5 flex flex-wrap gap-x-5 gap-y-2 border-t border-slate-100 pt-4 text-xs text-slate-500">
                    <span><strong className="text-slate-800">{school.minimumTransferCredits}</strong> sample minimum credits</span>
                    <span><strong className="text-slate-800">{school.preferredCreditRange[0]}–{school.preferredCreditRange[1]}</strong> preferred range</span>
                    <span><strong className="text-slate-800">{school.maximumTransferCredits}</strong> max lower-division credit</span>
                  </div>
                </div>
              </article>
            );
          })}

          {targets.length < schoolCatalog.length && (
            <div className="card flex flex-col gap-3 p-4 sm:flex-row sm:items-center">
              <div className="relative flex-1"><select aria-label="School to add" className="field appearance-none pr-9" value={schoolToAdd} onChange={(event) => setSchoolToAdd(event.target.value)}>{schoolCatalog.filter((school) => !targets.some((target) => target.schoolId === school.id)).map((school) => <option key={school.id} value={school.id}>{school.name}</option>)}</select><ChevronDown className="pointer-events-none absolute right-3 top-3.5 size-4 text-slate-400" /></div>
              <button onClick={addSchool} disabled={!schoolToAdd} className="secondary-button"><Plus className="size-4" /> Add another school</button>
            </div>
          )}

          <div className="flex flex-col-reverse justify-between gap-3 pt-2 sm:flex-row"><button onClick={() => router.push("/transcript")} className="secondary-button">Back</button><button disabled={!canContinue} onClick={() => router.push("/dashboard")} className="primary-button">Analyze {selectedPrograms} program{selectedPrograms === 1 ? "" : "s"} <ArrowRight className="size-4" /></button></div>
        </section>

        <aside className="space-y-4">
          <div className="card p-5 lg:sticky lg:top-24">
            <p className="text-xs font-bold uppercase tracking-[0.14em] text-slate-400">Comparison set</p>
            <div className="mt-4 grid grid-cols-2 gap-3"><div className="rounded-xl bg-slate-50 p-3"><p className="text-2xl font-semibold tracking-tight text-[var(--ink)]">{targets.length}</p><p className="text-xs text-slate-500">schools</p></div><div className="rounded-xl bg-slate-50 p-3"><p className="text-2xl font-semibold tracking-tight text-[var(--ink)]">{selectedPrograms}</p><p className="text-xs text-slate-500">programs</p></div></div>
            <div className="mt-5 space-y-3">{targets.flatMap((target) => target.majorIds.map((majorId) => ({ school: getSchool(target.schoolId), major: getMajor(majorId) }))).map(({ school, major }) => <div key={major?.id} className="flex items-center gap-2.5"><span className="size-2 rounded-full" style={{ backgroundColor: school?.color }} /><div><p className="text-sm font-medium text-slate-800">{major?.name}</p><p className="text-[11px] text-slate-400">{school?.shortName}</p></div></div>)}</div>
            <div className="my-5 h-px bg-slate-100" />
            <p className="text-xs leading-5 text-slate-500">Recommendations will rank courses by how many of these selected programs they support.</p>
          </div>
          <SampleDataBanner compact />
        </aside>
      </div>
    </main>
  );
}
