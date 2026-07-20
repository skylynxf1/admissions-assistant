"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Check, MapPin, Search, Star } from "lucide-react";
import { useApp } from "@/components/app-provider";
import { PipAssistant } from "@/components/ui";
import { getSchool, schoolCatalog } from "@/data/sample-policies";

const planAccents = ["var(--plan-a)", "var(--plan-b)", "var(--plan-c)", "var(--plan-d)"];

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
    <main className="mx-auto max-w-[1040px] px-5 py-10 lg:px-16 lg:py-10">
      <div className="rise grid items-end gap-6 sm:grid-cols-[1fr_190px]">
        <div>
          <h1 className="text-[32px] font-extrabold leading-[38px] text-[var(--forest)] sm:text-[42px] sm:leading-[48px]">Where could this path lead?</h1>
          <p className="mt-2.5 max-w-[560px] text-[var(--muted-ink)]">Pick any schools you’re curious about, then choose one priority to start with. Several destinations can share coursework — that’s a good thing.</p>
        </div>
        <PipAssistant pose="thinking" size={120} alt="Pip comparing two options" className="hidden sm:block" />
      </div>

      <div className="relative mx-auto mt-6 max-w-2xl">
        <Search className="pointer-events-none absolute left-4 top-3.5 size-5 text-[var(--muted-ink)]" />
        <input aria-label="Search schools" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search by school, city, or state…" className="field !rounded-[16px] !pl-12" />
      </div>

      <section className="mt-6 grid gap-4 sm:grid-cols-2">
        {filteredSchools.map((school) => {
          const selected = selectedIds.has(school.id);
          const priority = prioritySchoolId === school.id;
          const accent = planAccents[schoolCatalog.findIndex((item) => item.id === school.id) % planAccents.length];
          return (
            <article
              key={school.id}
              className={`overflow-hidden rounded-[var(--radius-card)] bg-white transition-all duration-[160ms] ${selected ? "border-2 border-[var(--path-green)] shadow-[var(--shadow-card),inset_0_0_0_4px_var(--mint-wash)]" : "border border-[var(--border)] shadow-[var(--shadow-card)] hover:-translate-y-0.5 hover:border-[var(--pip-mint)] hover:shadow-[var(--shadow-hover)]"}`}
            >
              <div style={{ borderTop: `5px solid ${selected ? accent : "transparent"}` }}>
                <button onClick={() => toggleSchool(school.id)} className="flex w-full items-start gap-3 px-5 pb-3 pt-4 text-left">
                  <span aria-hidden="true" className={`mt-0.5 grid size-[22px] shrink-0 place-items-center rounded-lg border-2 ${selected ? "border-[var(--path-green)] bg-[var(--path-green)] text-white" : "border-[var(--border)] bg-white text-transparent"}`}><Check className="size-3.5" /></span>
                  <span className="min-w-0 flex-1">
                    <span className="block text-[17px] font-bold leading-[23px] text-[var(--forest)]" style={{ fontFamily: "var(--font-heading)" }}>{school.name}</span>
                    <span className="mt-0.5 flex items-center gap-1 text-xs text-[var(--muted-ink)]" style={{ fontFamily: "var(--font-data)" }}><MapPin className="size-3" /> {school.location}</span>
                  </span>
                  {selected && <span className="text-xs font-semibold text-[var(--path-green)]">Remove</span>}
                </button>
                {selected && (
                  <div className="px-5 pb-4 pl-[52px]">
                    <button onClick={() => setPrioritySchoolId(school.id)} className={`flex w-full items-center gap-2 rounded-full border px-3.5 py-2 text-[13px] font-semibold transition ${priority ? "border-[var(--butter)] bg-[var(--surface-attention)] text-[#7A5B12]" : "border-[var(--border)] bg-white text-[var(--muted-ink)] hover:border-[var(--butter)] hover:text-[#7A5B12]"}`}>
                      <Star className={`size-4 ${priority ? "fill-[var(--butter)] text-[var(--butter)]" : "text-[var(--muted-ink)]"}`} />
                      {priority ? "Priority school" : "Make this my priority"}
                    </button>
                  </div>
                )}
              </div>
            </article>
          );
        })}
      </section>

      {filteredSchools.length === 0 && (
        <div className="mt-6 rounded-[var(--radius-card)] border-2 border-dotted border-[var(--border)] bg-white px-5 py-10 text-center">
          <PipAssistant pose="caution" size={88} alt="Pip looking unsure" />
          <p className="mt-3 text-sm text-[var(--muted-ink)]">No sample schools match “{query}”.</p>
        </div>
      )}

      <div className="card rise mt-7 flex flex-col gap-4 p-4 sm:flex-row sm:items-center sm:px-5">
        <div>
          <p className="text-sm font-semibold text-[var(--ink)]">{targets.length} school{targets.length === 1 ? "" : "s"} selected</p>
          <p className="mt-0.5 text-[13px] text-[var(--muted-ink)]">{prioritySchoolId ? `${getSchool(prioritySchoolId)?.shortName} is your priority.` : "Choose a priority school to continue."}</p>
        </div>
        <div className="flex gap-2.5 sm:ml-auto">
          <button onClick={() => router.push("/transcript")} className="secondary-button">Back</button>
          <button disabled={!canContinue} onClick={() => router.push("/program")} className="primary-button">Choose majors <ArrowRight className="size-4" /></button>
        </div>
      </div>
    </main>
  );
}
