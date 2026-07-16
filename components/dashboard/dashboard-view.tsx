"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import {
  AlertTriangle, BookOpen, Check, ChevronDown, Download, ExternalLink, GripVertical,
  LayoutGrid, Link2, MessageCircle, Plus, Settings2, SlidersHorizontal, Target, X,
} from "lucide-react";
import { useApp } from "@/components/app-provider";
import { AdvisorPanel } from "@/components/dashboard/advisor-panel";
import { EmptyState, ProgressBar, StateBadge } from "@/components/ui";
import { getMajor, getSchool } from "@/data/sample-policies";
import type { CourseRecommendation, InstitutionType, TargetSchool } from "@/lib/types";

type PlannerTab = "plan" | "requirements" | "paths" | "sources";
type WidgetId = "library" | "suggestions" | "prerequisites" | "progress";

interface PlannerTerm {
  id: string;
  label: string;
  note: string;
}

const initialTerms: PlannerTerm[] = [
  { id: "fall-2026", label: "Fall 2026", note: "Next term" },
  { id: "winter-2027", label: "Winter 2027", note: "Planned" },
  { id: "spring-2027", label: "Spring 2027", note: "Planned" },
];

const institutionLabels: Record<InstitutionType, string> = {
  "in-state-community-college": "In-state community college",
  "out-of-state-community-college": "Out-of-state community college",
  "in-state-four-year": "In-state four-year",
  "out-of-state-four-year": "Out-of-state four-year",
  international: "International university",
};

const widgetLabels: Record<WidgetId, { title: string; description: string }> = {
  library: { title: "Course library", description: "Drag courses into a quarter" },
  suggestions: { title: "Smart suggestions", description: "Courses that do more than one job" },
  prerequisites: { title: "Prerequisite map", description: "See what each course unlocks" },
  progress: { title: "Credit progress", description: "A short summary of your record" },
};

function PlannerLoading() {
  return <main className="mx-auto max-w-[1440px] px-5 py-10 lg:px-8"><div className="skeleton h-10 w-72" /><div className="mt-8 grid gap-4 lg:grid-cols-3">{[1, 2, 3].map((item) => <div key={item} className="skeleton h-72" />)}</div></main>;
}

function MajorPicker({ targets, prioritySchoolId, onChange, onClose }: { targets: TargetSchool[]; prioritySchoolId: string; onChange: (targets: TargetSchool[]) => void; onClose: () => void }) {
  const totalSelected = targets.reduce((sum, target) => sum + target.majorIds.length, 0);
  const toggle = (schoolId: string, majorId: string) => {
    const alreadySelected = targets.some((target) => target.schoolId === schoolId && target.majorIds.includes(majorId));
    if (alreadySelected && totalSelected === 1) return;
    onChange(targets.map((target) => target.schoolId === schoolId
      ? { ...target, majorIds: alreadySelected ? target.majorIds.filter((id) => id !== majorId) : [...target.majorIds, majorId] }
      : target));
  };

  return (
    <div className="fixed inset-0 z-[60] grid place-items-center bg-slate-950/30 p-4 backdrop-blur-sm" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
      <div className="w-full max-w-2xl overflow-hidden rounded-2xl bg-white shadow-2xl">
        <header className="flex items-center justify-between border-b border-slate-200 px-5 py-4"><div><h2 className="font-semibold text-slate-900">Majors in this plan</h2><p className="mt-1 text-xs text-slate-500">Add or remove majors. Recommendations update automatically.</p></div><button onClick={onClose} aria-label="Close majors" className="rounded-lg p-2 text-slate-400 hover:bg-slate-100"><X className="size-5" /></button></header>
        <div className="max-h-[65vh] space-y-5 overflow-y-auto p-5">
          {targets.map((target) => {
            const school = getSchool(target.schoolId);
            if (!school) return null;
            return <section key={school.id}><div className="flex items-center gap-2"><h3 className="text-sm font-semibold text-slate-900">{school.shortName}</h3>{school.id === prioritySchoolId && <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-amber-800">Priority</span>}</div><div className="mt-3 grid gap-2 sm:grid-cols-2">{school.majors.map((major) => { const selected = target.majorIds.includes(major.id); return <button key={major.id} onClick={() => toggle(school.id, major.id)} className={`flex items-center gap-3 rounded-xl border p-3 text-left transition ${selected ? "border-teal-400 bg-teal-50" : "border-slate-200 hover:border-slate-300"}`}><span className={`grid size-5 shrink-0 place-items-center rounded-md border ${selected ? "border-teal-600 bg-teal-600 text-white" : "border-slate-300 text-transparent"}`}><Check className="size-3" /></span><span><span className="block text-sm font-semibold text-slate-800">{major.name}</span><span className="mt-0.5 block text-[10px] text-slate-400">{major.admissionType.replaceAll("-", " ")}</span></span></button>; })}</div></section>;
          })}
        </div>
        <footer className="flex items-center justify-between border-t border-slate-200 px-5 py-4"><p className="text-xs text-slate-500">{totalSelected} major{totalSelected === 1 ? "" : "s"} selected</p><button onClick={onClose} className="primary-button">Done</button></footer>
      </div>
    </div>
  );
}

function SettingsPanel({ onClose }: { onClose: () => void }) {
  const { scenario, updateScenario } = useApp();
  return <div className="fixed inset-0 z-[60] grid place-items-center bg-slate-950/30 p-4 backdrop-blur-sm" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}><div className="w-full max-w-md rounded-2xl bg-white p-5 shadow-2xl"><div className="flex items-center justify-between"><div><h2 className="font-semibold text-slate-900">Plan settings</h2><p className="mt-1 text-xs text-slate-500">These change the sample analysis.</p></div><button onClick={onClose} aria-label="Close settings" className="rounded-lg p-2 text-slate-400 hover:bg-slate-100"><X className="size-5" /></button></div><div className="mt-5 space-y-4"><label><span className="field-label">Current-school type</span><select className="field" value={scenario.institutionType} onChange={(event) => updateScenario({ institutionType: event.target.value as InstitutionType })}>{Object.entries(institutionLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label><label><span className="field-label">Residency</span><select className="field" value={scenario.residency} onChange={(event) => updateScenario({ residency: event.target.value as typeof scenario.residency })}><option value="in-state">In-state</option><option value="out-of-state">Out-of-state</option><option value="international">International</option></select></label><label><span className="field-label">Preferred term load</span><select className="field" value={scenario.preferredCreditLoad} onChange={(event) => updateScenario({ preferredCreditLoad: Number(event.target.value) })}><option value={10}>10 credits</option><option value={12}>12 credits</option><option value={15}>15 credits</option><option value={18}>18 credits</option></select></label><button onClick={() => updateScenario({ useExamCredit: !scenario.useExamCredit })} className={`flex w-full items-center justify-between rounded-xl border px-4 py-3 text-sm font-semibold ${scenario.useExamCredit ? "border-teal-300 bg-teal-50 text-teal-800" : "border-slate-200 text-slate-600"}`}><span>Use AP / IB credit</span><span>{scenario.useExamCredit ? "On" : "Off"}</span></button></div><button onClick={onClose} className="primary-button mt-6 w-full">Apply settings</button></div></div>;
}

export function DashboardView() {
  const { targets, setTargets, prioritySchoolId, analysis, analysisStatus } = useApp();
  const [tab, setTab] = useState<PlannerTab>("plan");
  const [majorPickerOpen, setMajorPickerOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [advisorOpen, setAdvisorOpen] = useState(false);
  const [workspaceOpen, setWorkspaceOpen] = useState(false);
  const [terms, setTerms] = useState<PlannerTerm[]>(initialTerms);
  const [schedule, setSchedule] = useState<Record<string, string[]>>({ "fall-2026": [], "winter-2027": [], "spring-2027": [] });
  const [widgetOrder, setWidgetOrder] = useState<WidgetId[]>(["library", "suggestions", "prerequisites", "progress"]);
  const [widgetVisibility, setWidgetVisibility] = useState<Record<WidgetId, boolean>>({ library: true, suggestions: true, prerequisites: true, progress: true });
  const [activeMajorId, setActiveMajorId] = useState("");

  const prioritySchool = getSchool(prioritySchoolId);
  const selectedMajorIds = targets.flatMap((target) => target.majorIds);
  const selectedMajors = selectedMajorIds.map(getMajor).filter(Boolean);
  const selectedCourseIds = useMemo(() => new Set(Object.values(schedule).flat()), [schedule]);
  const courseById = useMemo(() => new Map((analysis?.recommendations ?? []).map((course) => [course.id, course])), [analysis]);

  if (!analysis && analysisStatus === "analyzing") return <PlannerLoading />;
  if (!analysis) return <main className="mx-auto max-w-xl px-5 py-20"><EmptyState title="Choose at least one major" description="Start with a major at your priority school, then the planner can build a course path." /><div className="mt-5 text-center"><Link href="/program" className="primary-button">Choose a major</Link></div></main>;

  const activeRequirementMajor = selectedMajorIds.includes(activeMajorId) ? activeMajorId : selectedMajorIds[0];
  const activeRequirements = analysis.requirements.filter((requirement) => requirement.majorId === activeRequirementMajor);
  const unscheduledCourses = analysis.recommendations.filter((course) => !selectedCourseIds.has(course.id));

  const startCourseDrag = (event: React.DragEvent, courseId: string) => {
    event.dataTransfer.setData("application/x-pathwise-course", courseId);
    event.dataTransfer.effectAllowed = "move";
  };

  const dropCourse = (event: React.DragEvent, termId: string) => {
    event.preventDefault();
    const courseId = event.dataTransfer.getData("application/x-pathwise-course");
    if (!courseById.has(courseId)) return;
    setSchedule((current) => {
      const next = Object.fromEntries(Object.entries(current).map(([id, ids]) => [id, ids.filter((item) => item !== courseId)]));
      next[termId] = [...(next[termId] ?? []), courseId];
      return next;
    });
  };

  const removeCourse = (termId: string, courseId: string) => setSchedule((current) => ({ ...current, [termId]: current[termId].filter((id) => id !== courseId) }));

  const addToOpenTerm = (courseId: string) => {
    const nextTerm = [...terms].sort((a, b) => (schedule[a.id]?.length ?? 0) - (schedule[b.id]?.length ?? 0))[0];
    if (!nextTerm) return;
    setSchedule((current) => ({ ...current, [nextTerm.id]: [...(current[nextTerm.id] ?? []).filter((id) => id !== courseId), courseId] }));
  };

  const addTerm = () => {
    if (terms.some((term) => term.id === "summer-2027")) return;
    setTerms((current) => [...current, { id: "summer-2027", label: "Summer 2027", note: "Optional" }]);
    setSchedule((current) => ({ ...current, "summer-2027": [] }));
  };

  const moveWidget = (event: React.DragEvent, targetId: WidgetId) => {
    event.preventDefault();
    const sourceId = event.dataTransfer.getData("application/x-pathwise-widget") as WidgetId;
    if (!sourceId || sourceId === targetId || !widgetOrder.includes(sourceId)) return;
    setWidgetOrder((current) => {
      const next = [...current];
      const sourceIndex = next.indexOf(sourceId);
      const targetIndex = next.indexOf(targetId);
      [next[sourceIndex], next[targetIndex]] = [next[targetIndex], next[sourceIndex]];
      return next;
    });
  };

  const courseCard = (course: CourseRecommendation, compact = false) => (
    <div key={course.id} data-course-id={course.id} draggable onDragStart={(event) => startCourseDrag(event, course.id)} className={`group cursor-grab rounded-xl border border-slate-200 bg-white shadow-sm transition hover:border-teal-300 hover:shadow-md active:cursor-grabbing ${compact ? "p-3" : "p-4"}`}>
      <div className="flex items-start gap-2"><GripVertical className="mt-0.5 size-4 shrink-0 text-slate-300" /><div className="min-w-0 flex-1"><p className="text-xs font-bold text-teal-700">{course.course}</p><p className="mt-0.5 text-sm font-semibold text-slate-900">{course.title}</p><div className="mt-2 flex flex-wrap gap-1">{course.satisfies.slice(0, 2).map((item) => <span key={item} className="rounded-md bg-slate-100 px-1.5 py-0.5 text-[9px] font-medium text-slate-500">{item}</span>)}</div></div><span className="text-[10px] font-semibold text-slate-400">{course.credits} cr</span></div>
    </div>
  );

  const renderWidget = (widgetId: WidgetId) => {
    const labels = widgetLabels[widgetId];
    let content: React.ReactNode;
    if (widgetId === "library") {
      content = <div className="space-y-2">{unscheduledCourses.length ? unscheduledCourses.map((course) => courseCard(course, true)) : <p className="rounded-xl bg-emerald-50 p-4 text-xs text-emerald-700">All suggested courses are on your board.</p>}</div>;
    } else if (widgetId === "suggestions") {
      content = <div className="space-y-3">{analysis.recommendations.slice(0, 3).map((course) => <div key={course.id} className="rounded-xl bg-teal-50/70 p-3"><div className="flex items-start justify-between gap-3"><div><p className="text-xs font-bold text-teal-800">{course.course}</p><p className="mt-0.5 text-sm font-semibold text-slate-900">{course.title}</p></div><button onClick={() => addToOpenTerm(course.id)} className="grid size-7 shrink-0 place-items-center rounded-lg bg-white text-teal-700 shadow-sm" aria-label={`Add ${course.course} to plan`}><Plus className="size-3.5" /></button></div><p className="mt-2 text-[11px] leading-4 text-slate-600">Meets {course.satisfies.join(" + ")}.</p></div>)}</div>;
    } else if (widgetId === "prerequisites") {
      content = <div className="space-y-4">{analysis.prerequisiteChains.slice(0, 2).map((chain) => <div key={chain.id}><p className="text-xs font-semibold text-slate-800">To reach {chain.targetCourse}</p><div className="mt-2 flex flex-wrap items-center gap-1.5">{chain.steps.map((step, index) => <div key={step.course} className="flex items-center gap-1.5"><span className={`rounded-lg px-2 py-1.5 text-[10px] font-semibold ${step.state === "complete" ? "bg-emerald-50 text-emerald-700" : step.state === "in-progress" ? "bg-blue-50 text-blue-700" : "bg-slate-100 text-slate-600"}`}>{step.course}</span>{index < chain.steps.length - 1 && <span className="text-slate-300">→</span>}</div>)}</div></div>)}</div>;
    } else {
      content = <div className="grid grid-cols-3 gap-2">{[["Earned", analysis.creditSummary.earned], ["Transfer", analysis.creditSummary.estimatedTransferable], ["Degree", analysis.creditSummary.degreeApplicable]].map(([label, value]) => <div key={label as string} className="rounded-xl bg-slate-50 p-3 text-center"><p className="text-xl font-semibold tracking-tight text-[var(--ink)]">{value as number}</p><p className="mt-1 text-[10px] text-slate-400">{label as string}</p></div>)}</div>;
    }
    return <section key={widgetId} onDragOver={(event) => event.preventDefault()} onDrop={(event) => moveWidget(event, widgetId)} className="card min-h-56 overflow-hidden"><header draggable onDragStart={(event) => { event.dataTransfer.setData("application/x-pathwise-widget", widgetId); event.dataTransfer.effectAllowed = "move"; }} className="flex cursor-move items-center gap-3 border-b border-slate-100 px-4 py-3"><GripVertical className="size-4 text-slate-300" /><div><h3 className="text-sm font-semibold text-slate-900">{labels.title}</h3><p className="text-[10px] text-slate-400">{labels.description}</p></div></header><div className="p-4">{content}</div></section>;
  };

  const tabs: Array<{ id: PlannerTab; label: string; Icon: typeof LayoutGrid }> = [
    { id: "plan", label: "My plan", Icon: LayoutGrid },
    { id: "requirements", label: "Requirements", Icon: BookOpen },
    { id: "paths", label: "Majors & paths", Icon: Target },
    { id: "sources", label: "Sources", Icon: Link2 },
  ];

  return <>
    <div className="print-hide sticky top-16 z-30 border-b border-slate-200 bg-white/95 backdrop-blur-xl">
      <div className="mx-auto flex max-w-[1440px] flex-col gap-3 px-5 py-3 lg:flex-row lg:items-center lg:px-8">
        <div className="flex min-w-0 items-center gap-3 lg:mr-4"><div className="grid size-9 shrink-0 place-items-center rounded-xl text-xs font-bold text-white" style={{ backgroundColor: prioritySchool?.color }}>{prioritySchool?.shortName.slice(0, 2).toUpperCase()}</div><div className="min-w-0"><p className="truncate text-sm font-semibold text-slate-900">{prioritySchool?.shortName}</p><p className="truncate text-[10px] text-slate-400">{selectedMajors.map((major) => major?.name).join(" · ")}</p></div></div>
        <nav className="flex flex-1 gap-1 overflow-x-auto">{tabs.map(({ id, label, Icon }) => <button key={id} onClick={() => setTab(id)} className={`flex shrink-0 items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-semibold transition ${tab === id ? "bg-[var(--ink)] text-white" : "text-slate-500 hover:bg-slate-100"}`}><Icon className="size-3.5" /> {label}</button>)}</nav>
        <div className="flex items-center gap-2"><button onClick={() => setMajorPickerOpen(true)} className="secondary-button !min-h-9 !px-3 !py-1.5"><Plus className="size-3.5" /> Majors <span className="rounded-full bg-slate-100 px-1.5 text-[10px] text-slate-500">{selectedMajorIds.length}</span></button><button onClick={() => setSettingsOpen(true)} aria-label="Plan settings" className="secondary-button !min-h-9 !px-2.5 !py-1.5"><Settings2 className="size-4" /></button><button onClick={() => window.print()} className="primary-button !min-h-9 !px-3 !py-1.5"><Download className="size-3.5" /> Export PDF</button></div>
      </div>
    </div>

    <main className="mx-auto max-w-[1440px] px-5 pb-28 pt-7 lg:px-8">
      {tab === "plan" && <>
        <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end"><div><p className="text-xs font-bold uppercase tracking-[0.15em] text-teal-700">Editable planning playground</p><h1 className="mt-2 text-3xl font-semibold tracking-[-0.045em] text-[var(--ink)]">Build a plan that keeps options open.</h1><p className="mt-2 text-sm text-slate-500">Drag courses into quarters. Move them anytime. Suggestions update with your selected majors.</p></div><div className="rounded-xl bg-amber-50 px-3 py-2 text-xs text-amber-800">Sample policy data · not verified</div></div>

        <section className="card mt-6 overflow-hidden">
          <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4"><div><h2 className="font-semibold text-slate-900">Quarter plan</h2><p className="mt-1 text-xs text-slate-500">Drop a course into any term.</p></div><button onClick={addTerm} className="secondary-button !min-h-9 !px-3 !py-1.5"><Plus className="size-3.5" /> Add summer</button></div>
          <div className="grid gap-3 p-4 md:grid-cols-2 xl:grid-cols-4">
            {terms.map((term) => {
              const courseIds = schedule[term.id] ?? [];
              const credits = courseIds.reduce((sum, id) => sum + (courseById.get(id)?.credits ?? 0), 0);
              return <div key={term.id} data-term-id={term.id} onDragOver={(event) => event.preventDefault()} onDrop={(event) => dropCourse(event, term.id)} className="min-h-64 rounded-2xl border border-dashed border-slate-300 bg-slate-50/70 p-3 transition hover:border-teal-400 hover:bg-teal-50/40"><div className="flex items-start justify-between"><div><h3 className="text-sm font-semibold text-slate-900">{term.label}</h3><p className="mt-0.5 text-[10px] text-slate-400">{term.note}</p></div><span className="rounded-full bg-white px-2 py-1 text-[10px] font-semibold text-slate-500 shadow-sm">{credits} cr</span></div><div className="mt-3 space-y-2">{courseIds.map((courseId) => { const course = courseById.get(courseId); if (!course) return null; return <div key={courseId} draggable onDragStart={(event) => startCourseDrag(event, courseId)} className="group rounded-xl border border-slate-200 bg-white p-3 shadow-sm"><div className="flex items-start gap-2"><GripVertical className="mt-0.5 size-3.5 text-slate-300" /><div className="min-w-0 flex-1"><p className="text-xs font-bold text-teal-700">{course.course}</p><p className="mt-0.5 truncate text-xs font-semibold text-slate-800">{course.title}</p><p className="mt-1 text-[9px] text-slate-400">{course.satisfies[0]}</p></div><button onClick={() => removeCourse(term.id, courseId)} aria-label={`Remove ${course.course} from ${term.label}`} className="text-slate-300 hover:text-rose-500"><X className="size-3.5" /></button></div></div>; })}{courseIds.length === 0 && <div className="grid min-h-40 place-items-center rounded-xl text-center"><div><Plus className="mx-auto size-5 text-slate-300" /><p className="mt-2 text-[11px] text-slate-400">Drop a course here</p></div></div>}</div></div>;
            })}
          </div>
        </section>

        <div className="mt-5 grid gap-5 lg:grid-cols-2">{widgetOrder.filter((id) => widgetVisibility[id]).map(renderWidget)}</div>
      </>}

      {tab === "requirements" && <section><div className="max-w-2xl"><p className="text-xs font-bold uppercase tracking-[0.15em] text-teal-700">What still needs attention</p><h1 className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-[var(--ink)]">Requirements, in plain language.</h1><p className="mt-2 text-sm text-slate-500">Choose a major to see only the requirements that matter for that path.</p></div><div className="mt-6 flex flex-wrap gap-2">{selectedMajorIds.map((majorId) => <button key={majorId} onClick={() => setActiveMajorId(majorId)} className={`rounded-full px-3 py-2 text-xs font-semibold ${activeRequirementMajor === majorId ? "bg-[var(--ink)] text-white" : "border border-slate-200 bg-white text-slate-600"}`}>{getMajor(majorId)?.name}</button>)}</div><div className="mt-5 grid gap-3 lg:grid-cols-2">{activeRequirements.map((requirement) => { const percent = requirement.requiredCredits ? Math.min((requirement.completedCredits / requirement.requiredCredits) * 100, 100) : 0; return <article key={requirement.id} className="card p-5"><div className="flex items-start justify-between gap-3"><div><p className="text-[10px] font-bold uppercase tracking-wide text-slate-400">{requirement.category}</p><h2 className="mt-1 text-sm font-semibold text-slate-900">{requirement.title}</h2></div><StateBadge state={requirement.state} /></div><div className="mt-4"><ProgressBar value={percent} tone={requirement.state === "uncertain" ? "amber" : "teal"} /></div><p className="mt-3 text-xs text-slate-500">{requirement.missingCourses.length ? `Next: ${requirement.missingCourses.join(", ")}` : `Covered by ${requirement.matchedCourses.join(", ") || "your current record"}.`}</p></article>; })}</div>{analysis.alerts.some((alert) => alert.canDraftEmail) && <div className="mt-5 flex items-start gap-3 rounded-2xl border border-amber-200 bg-amber-50 p-4"><AlertTriangle className="mt-0.5 size-4 text-amber-600" /><div><p className="text-sm font-semibold text-amber-950">One item still needs confirmation</p><p className="mt-1 text-xs leading-5 text-amber-800">The programming equivalency is not confirmed by the sample policy dataset. Ask the advisor for the exact question to send the department.</p><button onClick={() => setAdvisorOpen(true)} className="mt-2 text-xs font-semibold text-amber-900 underline">Ask about this</button></div></div>}</section>}

      {tab === "paths" && <section><div className="max-w-2xl"><p className="text-xs font-bold uppercase tracking-[0.15em] text-teal-700">Majors & paths</p><h1 className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-[var(--ink)]">See how each option is shaping up.</h1><p className="mt-2 text-sm text-slate-500">Readiness shows preparation—not admission probability.</p></div><div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">{analysis.readiness.map((item) => { const school = getSchool(item.schoolId); const major = getMajor(item.majorId); return <article key={item.majorId} className="card p-5"><div className="flex items-start justify-between"><div><p className="text-xs text-slate-400">{school?.shortName}</p><h2 className="mt-1 font-semibold text-slate-900">{major?.name}</h2></div><span className="text-2xl font-semibold tracking-tight text-[var(--ink)]">{item.score}</span></div><div className="mt-4"><ProgressBar value={item.score} tone={item.score >= 60 ? "teal" : "amber"} /></div><div className="mt-4 grid grid-cols-2 gap-2 text-[10px]"><div className="rounded-lg bg-slate-50 p-2"><span className="block text-slate-400">Prereqs</span><strong className="mt-1 block text-slate-700">{item.completedPrerequisites}/{item.totalPrerequisites}</strong></div><div className="rounded-lg bg-slate-50 p-2"><span className="block text-slate-400">Credit minimum</span><strong className={`mt-1 block ${item.creditMinimumMet ? "text-emerald-700" : "text-rose-700"}`}>{item.creditMinimumMet ? "Met" : "Not yet"}</strong></div></div></article>; })}</div><button onClick={() => setMajorPickerOpen(true)} className="secondary-button mt-5"><Plus className="size-4" /> Add another major</button></section>}

      {tab === "sources" && <section><div className="max-w-2xl"><p className="text-xs font-bold uppercase tracking-[0.15em] text-teal-700">Grounding</p><h1 className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-[var(--ink)]">The data behind this plan.</h1><p className="mt-2 text-sm text-slate-500">The advisor is restricted to these saved policy records and your transcript. In this prototype, they are unverified sample records.</p></div><div className="mt-6 grid gap-3 md:grid-cols-2">{analysis.citations.map((citation) => <a key={citation.id} href={citation.url} target="_blank" rel="noreferrer" className="card group flex items-start gap-3 p-4 hover:border-teal-300"><div className="grid size-9 shrink-0 place-items-center rounded-xl bg-slate-100 text-slate-500 group-hover:bg-teal-50 group-hover:text-teal-700"><ExternalLink className="size-4" /></div><div><h2 className="text-sm font-semibold text-slate-900">{citation.title}</h2><p className="mt-1 text-xs text-slate-500">{citation.publisher}</p><p className="mt-2 text-[10px] font-semibold text-amber-700">Sample record · not live-scraped yet</p></div></a>)}</div></section>}
    </main>

    <div className="print-hide fixed bottom-5 left-1/2 z-40 -translate-x-1/2">
      {workspaceOpen && <div className="absolute bottom-14 left-1/2 w-64 -translate-x-1/2 rounded-2xl border border-slate-200 bg-white p-3 shadow-2xl"><p className="px-2 pb-2 text-[10px] font-bold uppercase tracking-wide text-slate-400">Visible workspace panels</p>{(Object.keys(widgetLabels) as WidgetId[]).map((id) => <button key={id} onClick={() => setWidgetVisibility((current) => ({ ...current, [id]: !current[id] }))} className="flex w-full items-center gap-3 rounded-xl px-2 py-2 text-left hover:bg-slate-50"><span className={`grid size-5 place-items-center rounded-md border ${widgetVisibility[id] ? "border-teal-600 bg-teal-600 text-white" : "border-slate-300 text-transparent"}`}><Check className="size-3" /></span><span><span className="block text-xs font-semibold text-slate-800">{widgetLabels[id].title}</span><span className="block text-[9px] text-slate-400">{widgetLabels[id].description}</span></span></button>)}</div>}
      <div className="flex items-center gap-1 rounded-2xl border border-slate-200 bg-white p-1.5 shadow-xl shadow-slate-900/10"><button onClick={() => setWorkspaceOpen((open) => !open)} className={`flex items-center gap-2 rounded-xl px-3 py-2 text-xs font-semibold ${workspaceOpen ? "bg-[var(--ink)] text-white" : "text-slate-600 hover:bg-slate-100"}`}><SlidersHorizontal className="size-4" /> Workspace <ChevronDown className={`size-3 transition ${workspaceOpen ? "rotate-180" : ""}`} /></button><span className="h-6 w-px bg-slate-200" /><button onClick={() => setAdvisorOpen(true)} className="flex items-center gap-2 rounded-xl px-3 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100"><MessageCircle className="size-4 text-teal-600" /> Ask advisor</button></div>
    </div>

    <AdvisorPanel open={advisorOpen} onClose={() => setAdvisorOpen(false)} />
    {majorPickerOpen && <MajorPicker targets={targets} prioritySchoolId={prioritySchoolId} onChange={setTargets} onClose={() => setMajorPickerOpen(false)} />}
    {settingsOpen && <SettingsPanel onClose={() => setSettingsOpen(false)} />}
  </>;
}
