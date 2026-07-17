"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Check, MapPin, Search, Star } from "lucide-react";
import { useApp } from "@/components/app-provider";
import { getSchool, schoolCatalog } from "@/data/sample-policies";

export default function TargetsPage() {
  const router = useRouter();
  const { targets, setTargets, prioritySchoolId, setPrioritySchoolId } = useApp();
  const [query, setQuery] = useState("");
  const selectedIds = useMemo(() => new Set(targets.map((target) => target.schoolId)), [targets]);
  const filteredSchools = useMemo(() => {
    const clean = query.trim().toLowerCase();
    if (!clean) return schoolCatalog;
    return schoolCatalog.filter((school) => `${school.name} ${school.shortName} ${school.location}`.toLowerCase().includes(clean));
  }, [query]);

  const toggleSchool = (schoolId: string) => {
    if (selectedIds.has(schoolId)) {
      const next = targets.filter((target) => target.schoolId !== schoolId);
      setTargets(next);
      if (prioritySchoolId === schoolId) setPrioritySchoolId(next[0]?.schoolId || "");
      return;
    }
    const next = [...targets, { schoolId, majorIds: [] }];
    setTargets(next);
    if (!prioritySchoolId) setPrioritySchoolId(schoolId);
  };

  const canContinue = targets.length > 0 && selectedIds.has(prioritySchoolId);

  return (
    <main className="mx-auto max-w-4xl px-5 py-10 lg:px-8 lg:py-12">
      <div className="text-center">
        <p className="text-xs font-bold uppercase tracking-[0.16em] text-teal-700">Destination schools</p>
        <h1 className="mt-3 text-3xl font-semibold tracking-[-0.045em] text-[var(--ink)] sm:text-4xl">Where are you interested in going?</h1>
        <p className="mx-auto mt-3 max-w-xl text-slate-500">Choose any schools you want to keep in the plan. Then pick one priority school to start with.</p>
      </div>

      <div className="relative mx-auto mt-8 max-w-2xl">
        <Search className="pointer-events-none absolute left-4 top-3.5 size-5 text-slate-400" />
        <input aria-label="Search schools" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search by school, city, or state…" className="field !rounded-2xl !py-3.5 !pl-12 text-base shadow-sm" />
      </div>

      <section className="mt-6 grid gap-3 sm:grid-cols-2">
        {filteredSchools.map((school) => {
          const selected = selectedIds.has(school.id);
          const priority = prioritySchoolId === school.id;
          return (
            <article key={school.id} className={`rounded-2xl border bg-white p-4 transition ${selected ? "border-teal-400 ring-2 ring-teal-100" : "border-slate-200 hover:border-slate-300"}`}>
              <button onClick={() => toggleSchool(school.id)} className="flex w-full items-start gap-3 text-left">
                <span className={`mt-0.5 grid size-6 shrink-0 place-items-center rounded-lg border transition ${selected ? "border-teal-600 bg-teal-600 text-white" : "border-slate-300 text-transparent"}`}><Check className="size-3.5" /></span>
                <span className="min-w-0 flex-1"><span className="block text-sm font-semibold text-slate-900">{school.name}</span><span className="mt-1 flex items-center gap-1 text-xs text-slate-500"><MapPin className="size-3" /> {school.location}</span></span>
              </button>
              {selected && (
                <button onClick={() => setPrioritySchoolId(school.id)} className={`mt-4 flex w-full items-center gap-2 rounded-xl px-3 py-2.5 text-xs font-semibold transition ${priority ? "bg-amber-50 text-amber-800 ring-1 ring-amber-200" : "bg-slate-50 text-slate-500 hover:bg-amber-50 hover:text-amber-800"}`}>
                  <Star className={`size-4 ${priority ? "fill-amber-400 text-amber-500" : "text-slate-400"}`} />
                  {priority ? "Priority school" : "Make this my priority"}
                </button>
              )}
            </article>
          );
        })}
      </section>

      {filteredSchools.length === 0 && <div className="mt-6 rounded-2xl border border-dashed border-slate-300 px-5 py-12 text-center text-sm text-slate-500">No sample schools match “{query}”.</div>}

      <div className="card mt-8 flex flex-col gap-4 p-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-semibold text-slate-900">{targets.length} school{targets.length === 1 ? "" : "s"} selected</p>
          <p className="mt-1 text-xs text-slate-500">{prioritySchoolId ? `${getSchool(prioritySchoolId)?.shortName} is your priority.` : "Choose a priority school to continue."}</p>
        </div>
        <div className="flex gap-2"><button onClick={() => router.push("/transcript")} className="secondary-button">Back</button><button disabled={!canContinue} onClick={() => router.push("/program")} className="primary-button">Choose majors <ArrowRight className="size-4" /></button></div>
      </div>
    </main>
  );
}
