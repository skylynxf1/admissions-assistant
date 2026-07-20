"use client";

import { useRouter } from "next/navigation";
import { ArrowRight, BookOpenCheck, Code2, GraduationCap, MapPin, Scale } from "lucide-react";
import { useApp } from "@/components/app-provider";
import { PipAssistant } from "@/components/ui";
import { getSchool } from "@/data/sample-policies";

export default function ProgramPage() {
  const router = useRouter();
  const { targets, setTargets, prioritySchoolId } = useApp();
  const school = getSchool(prioritySchoolId);
  const target = targets.find((item) => item.schoolId === prioritySchoolId);
  const selectedMajorIds = target?.majorIds ?? [];

  if (!school || !target) {
    return (
      <main className="mx-auto max-w-xl px-5 py-20 text-center">
        <PipAssistant pose="caution" size={110} alt="Pip pointing out a missing step" />
        <h1 className="mt-4 text-2xl font-extrabold text-[var(--forest)]">Choose a priority school first.</h1>
        <button onClick={() => router.push("/targets")} className="primary-button mt-5">Back to schools</button>
      </main>
    );
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
    <main className="mx-auto max-w-[1040px] px-5 py-10 lg:px-16 lg:py-10">
      <section className="card rise overflow-hidden">
        <div style={{ borderTop: "5px solid var(--plan-a)" }}>
          <div className="grid gap-8 p-6 sm:p-7 lg:grid-cols-[1fr_320px]">
            <div>
              <p className="text-[13px] font-semibold text-[var(--path-green)]">Your priority school</p>
              <h1 className="mt-2 text-[32px] font-extrabold leading-[38px] text-[var(--forest)] sm:text-[42px] sm:leading-[48px]">{school.name}</h1>
              <p className="mt-2 flex items-center gap-1.5 text-sm text-[var(--muted-ink)]" style={{ fontFamily: "var(--font-data)" }}><MapPin className="size-4" /> {school.location}</p>
              <div className="mt-7">
                <h2 className="text-[22px] font-bold leading-7 text-[var(--forest)]">What are you interested in studying?</h2>
                <p className="mt-1 text-sm text-[var(--muted-ink)]">Choose one or more majors. You can add more later from the planner.</p>
              </div>
              <div className="mt-4 flex flex-wrap gap-2.5">
                {school.majors.map((major) => {
                  const selected = selectedMajorIds.includes(major.id);
                  return (
                    <button
                      key={major.id}
                      onClick={() => toggleMajor(major.id)}
                      aria-pressed={selected}
                      className={`rounded-full border px-4 py-2.5 text-left text-sm font-semibold transition ${selected ? "border-[var(--path-green)] bg-[var(--mint-wash)] text-[var(--forest)]" : "border-[var(--border)] bg-white text-[var(--muted-ink)] hover:border-[var(--pip-mint)]"}`}
                    >
                      {selected ? "✓ " : ""}{major.name}
                      <span className={`ml-1.5 text-xs font-medium ${selected ? "text-[var(--path-green)]" : "text-[var(--muted-ink)]/70"}`}>{major.college}</span>
                    </button>
                  );
                })}
              </div>
            </div>
            <aside className="rounded-[var(--radius-nested)] border border-[var(--border)] bg-[var(--cream)] p-5">
              <h2 className="text-base font-bold text-[var(--forest)]">At a glance</h2>
              <p className="mt-1.5 text-xs leading-5 text-[var(--muted-ink)]">A short sample outline before we personalize it with your transcript.</p>
              <div className="mt-4 space-y-3">
                {outline.map(({ Icon, title, text }) => (
                  <div key={title} className="flex gap-3 rounded-[var(--radius-control)] bg-white p-3">
                    <div className="grid size-8 shrink-0 place-items-center rounded-[10px] bg-[var(--mint-wash)] text-[var(--forest)]"><Icon className="size-4" /></div>
                    <div>
                      <p className="text-xs font-bold text-[var(--forest)]">{title}</p>
                      <p className="mt-1 text-[11px] leading-4 text-[var(--muted-ink)]">{text}</p>
                    </div>
                  </div>
                ))}
              </div>
              <p className="mt-4 text-[11px] leading-4 text-[#7A5B12]">Sample data only. Policy details are not yet verified from a live scrape.</p>
            </aside>
          </div>
        </div>
      </section>

      <div className="card rise mt-6 flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:justify-between" style={{ background: "var(--gradient-hope)" }}>
        <div className="flex items-center gap-4">
          <PipAssistant pose="thumbs-up" size={72} alt="Pip giving a thumbs-up" />
          <div>
            <p className="font-bold text-[var(--forest)]" style={{ fontFamily: "var(--font-heading)" }}>Ready to apply this to your record?</p>
            <p className="mt-1 text-sm text-[var(--muted-ink)]">We’ll turn the outline into an editable quarter-by-quarter plan.</p>
          </div>
        </div>
        <button disabled={selectedMajorIds.length === 0} onClick={() => router.push("/dashboard")} className="cta-button shrink-0">Build my plan <ArrowRight className="size-4" /></button>
      </div>
    </main>
  );
}
