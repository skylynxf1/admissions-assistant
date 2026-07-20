"use client";

import { useMemo, useState } from "react";
import {
  AlertTriangle, BookOpenCheck, Check, GitCompareArrows, GraduationCap, Plus,
  RotateCcw, Trash2, TrendingUp, X,
} from "lucide-react";
import { useApp } from "@/components/app-provider";
import { getMajor, getSchool, schoolCatalog } from "@/data/sample-policies";
import type {
  CourseRecord, CourseStatus, ExamCredit, InstitutionType, PlanComparison,
  PlannedCourse, SimulationSummary,
} from "@/lib/types";

export interface SimulatorTerm {
  id: string;
  label: string;
  note: string;
}

const institutionLabels: Record<InstitutionType, string> = {
  "in-state-community-college": "In-state community college",
  "out-of-state-community-college": "Out-of-state community college",
  "in-state-four-year": "In-state four-year university",
  "out-of-state-four-year": "Out-of-state four-year university",
  international: "International university",
};

const transferTerms = ["Fall 2027", "Winter 2028", "Spring 2028", "Fall 2028", "Fall 2029"];
const graduationTerms = ["Spring 2029", "Fall 2029", "Spring 2030", "Fall 2030", "Spring 2031", "Fall 2031"];

function ModalFrame({ title, description, onClose, children, wide = false }: { title: string; description: string; onClose: () => void; children: React.ReactNode; wide?: boolean }) {
  return <div className="fixed inset-0 z-[70] grid place-items-center bg-slate-950/35 p-3 backdrop-blur-sm" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
    <div className={`flex max-h-[92vh] w-full flex-col overflow-hidden rounded-3xl bg-white shadow-2xl ${wide ? "max-w-5xl" : "max-w-xl"}`}>
      <header className="flex shrink-0 items-start justify-between border-b border-slate-200 px-5 py-4 sm:px-6">
        <div><h2 className="text-lg font-semibold tracking-tight text-slate-900">{title}</h2><p className="mt-1 text-xs text-slate-500">{description}</p></div>
        <button onClick={onClose} aria-label={`Close ${title.toLowerCase()}`} className="rounded-xl p-2 text-slate-400 hover:bg-slate-100"><X className="size-5" /></button>
      </header>
      {children}
    </div>
  </div>;
}

export function SchoolMajorPanel({ onClose }: { onClose: () => void }) {
  const { targets, setTargets, prioritySchoolId, setPrioritySchoolId } = useApp();
  const totalMajors = targets.reduce((sum, target) => sum + target.majorIds.length, 0);

  const toggleSchool = (schoolId: string) => {
    const selected = targets.some((target) => target.schoolId === schoolId);
    if (selected) {
      if (targets.length === 1) return;
      const next = targets.filter((target) => target.schoolId !== schoolId);
      setTargets(next);
      if (prioritySchoolId === schoolId) setPrioritySchoolId(next[0].schoolId);
      return;
    }
    const school = getSchool(schoolId);
    setTargets([...targets, { schoolId, majorIds: school?.majors[0] ? [school.majors[0].id] : [] }]);
  };

  const toggleMajor = (schoolId: string, majorId: string) => {
    const selected = targets.some((target) => target.schoolId === schoolId && target.majorIds.includes(majorId));
    if (selected && totalMajors === 1) return;
    setTargets(targets.map((target) => target.schoolId === schoolId
      ? { ...target, majorIds: selected ? target.majorIds.filter((id) => id !== majorId) : [...target.majorIds, majorId] }
      : target));
  };

  return <ModalFrame title="Universities and majors" description="Add schools, compare multiple majors, and choose the priority destination." onClose={onClose} wide>
    <div className="overflow-y-auto p-5 sm:p-6">
      <div className="grid gap-4 lg:grid-cols-3">
        {schoolCatalog.map((school) => {
          const target = targets.find((item) => item.schoolId === school.id);
          const selected = Boolean(target);
          return <article key={school.id} className={`rounded-2xl border p-4 ${selected ? "border-teal-300 bg-teal-50/40" : "border-slate-200"}`}>
            <div className="flex items-start justify-between gap-3">
              <button onClick={() => toggleSchool(school.id)} className="flex flex-1 items-start gap-3 text-left" aria-label={`${selected ? "Remove" : "Add"} ${school.name}`}>
                <span className={`mt-0.5 grid size-6 shrink-0 place-items-center rounded-lg border ${selected ? "border-teal-600 bg-teal-600 text-white" : "border-slate-300 text-transparent"}`}><Check className="size-3.5" /></span>
                <span><span className="block text-sm font-semibold text-slate-900">{school.shortName}</span><span className="mt-1 block text-[10px] text-slate-500">{school.location}</span></span>
              </button>
              {selected && <button onClick={() => setPrioritySchoolId(school.id)} className={`rounded-full px-2 py-1 text-[9px] font-bold uppercase tracking-wide ${prioritySchoolId === school.id ? "bg-amber-100 text-amber-800" : "bg-white text-slate-500"}`}>{prioritySchoolId === school.id ? "Priority" : "Make priority"}</button>}
            </div>
            {target && <div className="mt-4 space-y-2 border-t border-teal-100 pt-3">{school.majors.map((major) => {
              const checked = target.majorIds.includes(major.id);
              return <button key={major.id} onClick={() => toggleMajor(school.id, major.id)} className="flex w-full items-center gap-2 rounded-xl bg-white px-3 py-2 text-left shadow-sm">
                <span className={`grid size-4 shrink-0 place-items-center rounded border ${checked ? "border-teal-600 bg-teal-600 text-white" : "border-slate-300 text-transparent"}`}><Check className="size-2.5" /></span>
                <span className="min-w-0"><span className="block truncate text-xs font-semibold text-slate-800">{major.name}</span><span className="block text-[9px] text-slate-400">{major.admissionType.replaceAll("-", " ")}</span></span>
              </button>;
            })}</div>}
          </article>;
        })}
      </div>
      <p className="mt-4 text-xs text-slate-500">{targets.length} universities · {totalMajors} major{totalMajors === 1 ? "" : "s"} selected. At least one university and one major stay in the plan.</p>
    </div>
    <footer className="flex shrink-0 justify-end border-t border-slate-200 px-5 py-4"><button onClick={onClose} className="primary-button">Apply destinations</button></footer>
  </ModalFrame>;
}

export function SettingsPanel({ onClose }: { onClose: () => void }) {
  const { scenario, transcript, updateScenario, analysisStatus } = useApp();
  const institutions = useMemo(() => Array.from(new Set([...transcript.institutions, "Bellevue College", "Green River College", "Seattle University", "Washington State University"])), [transcript.institutions]);

  return <ModalFrame title="Scenario settings" description="Every change recalculates eligibility, credits, options, and the graduation timeline." onClose={onClose}>
    <div className="overflow-y-auto p-5 sm:p-6">
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="sm:col-span-2"><span className="field-label">Current school</span><select aria-label="Current school" className="field" value={scenario.currentInstitution} onChange={(event) => updateScenario({ currentInstitution: event.target.value })}>{institutions.map((institution) => <option key={institution}>{institution}</option>)}</select></label>
        <label><span className="field-label">School type</span><select aria-label="Current school type" className="field" value={scenario.institutionType} onChange={(event) => updateScenario({ institutionType: event.target.value as InstitutionType })}>{Object.entries(institutionLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
        <label><span className="field-label">Residency</span><select aria-label="Residency" className="field" value={scenario.residency} onChange={(event) => updateScenario({ residency: event.target.value as typeof scenario.residency })}><option value="in-state">In-state</option><option value="out-of-state">Out-of-state</option><option value="international">International</option></select></label>
        <label><span className="field-label">Intended enrollment term</span><select aria-label="Intended enrollment term" className="field" value={scenario.targetTransferTerm} onChange={(event) => updateScenario({ targetTransferTerm: event.target.value })}>{transferTerms.map((term) => <option key={term}>{term}</option>)}</select></label>
        <label><span className="field-label">Maximum credits per quarter</span><select aria-label="Maximum credits per quarter" className="field" value={scenario.preferredCreditLoad} onChange={(event) => updateScenario({ preferredCreditLoad: Number(event.target.value) })}>{[10, 12, 15, 18, 20].map((credits) => <option key={credits} value={credits}>{credits} credits</option>)}</select></label>
        <label className="sm:col-span-2"><span className="field-label">Graduation target</span><select aria-label="Graduation target" className="field" value={scenario.graduationTarget} onChange={(event) => updateScenario({ graduationTarget: event.target.value })}>{graduationTerms.map((term) => <option key={term}>{term}</option>)}</select></label>
      </div>
      <div className="mt-5 grid gap-3 sm:grid-cols-2">
        <button onClick={() => updateScenario({ useExamCredit: !scenario.useExamCredit })} className={`flex items-center justify-between rounded-xl border px-4 py-3 text-sm font-semibold ${scenario.useExamCredit ? "border-teal-300 bg-teal-50 text-teal-800" : "border-slate-200 text-slate-600"}`}><span>Apply AP / IB credit</span><span>{scenario.useExamCredit ? "On" : "Off"}</span></button>
        <button onClick={() => updateScenario({ attendSummer: !scenario.attendSummer })} className={`flex items-center justify-between rounded-xl border px-4 py-3 text-sm font-semibold ${scenario.attendSummer ? "border-teal-300 bg-teal-50 text-teal-800" : "border-slate-200 text-slate-600"}`}><span>Include summer terms</span><span>{scenario.attendSummer ? "On" : "Off"}</span></button>
      </div>
      <div className="mt-5 flex items-center gap-2 rounded-xl bg-slate-50 px-3 py-2 text-xs text-slate-500"><span className={`size-2 rounded-full ${analysisStatus === "analyzing" ? "animate-pulse bg-amber-500" : "bg-emerald-500"}`} />{analysisStatus === "analyzing" ? "Recalculating scenario…" : "Scenario is up to date"}</div>
    </div>
    <footer className="flex shrink-0 justify-end border-t border-slate-200 px-5 py-4"><button onClick={onClose} className="primary-button">Done</button></footer>
  </ModalFrame>;
}

const gradeOptions = ["A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", "F", "IP"];

export function AcademicRecordPanel({ onClose }: { onClose: () => void }) {
  const { transcript, setTranscript, scenario, updateScenario } = useApp();
  const [section, setSection] = useState<"courses" | "exams">("courses");
  const updateCourse = (id: string, updates: Partial<CourseRecord>) => setTranscript({ ...transcript, courses: transcript.courses.map((course) => {
    if (course.id !== id) return course;
    const next = { ...course, ...updates };
    if (updates.creditsAttempted !== undefined && next.status === "completed") next.creditsEarned = updates.creditsAttempted;
    if (updates.status === "completed" && next.creditsEarned === 0) next.creditsEarned = next.creditsAttempted;
    if (updates.status && updates.status !== "completed") next.creditsEarned = 0;
    return next;
  }) });
  const removeCourse = (id: string) => setTranscript({ ...transcript, courses: transcript.courses.filter((course) => course.id !== id) });
  const addCourse = () => setTranscript({ ...transcript, courses: [...transcript.courses, {
    id: `course-${Date.now()}`, institution: scenario.currentInstitution, code: "NEW 101", title: "New course", term: "Current term",
    creditsAttempted: 5, creditsEarned: 0, grade: "IP", status: "in-progress", confidence: "high", repeat: false, transfer: false,
  }] });
  const updateExam = (id: string, updates: Partial<ExamCredit>) => setTranscript({ ...transcript, examCredits: transcript.examCredits.map((exam) => exam.id === id ? { ...exam, ...updates } : exam) });
  const addExam = () => {
    const next: ExamCredit = { id: `exam-${Date.now()}`, type: "AP", subject: "New AP subject", score: "3", creditsAwarded: 3, enabled: true };
    setTranscript({ ...transcript, examCredits: [...transcript.examCredits, next] });
    updateScenario({ useExamCredit: true });
  };

  return <ModalFrame title="Academic record" description="Edit courses, grades, credit amounts, and AP/IB credit without leaving the simulator." onClose={onClose} wide>
    <div className="flex shrink-0 gap-1 border-b border-slate-200 px-5 pt-3"><button onClick={() => setSection("courses")} className={`rounded-t-xl px-4 py-2 text-xs font-semibold ${section === "courses" ? "bg-slate-100 text-slate-900" : "text-slate-500"}`}>College courses ({transcript.courses.length})</button><button onClick={() => setSection("exams")} className={`rounded-t-xl px-4 py-2 text-xs font-semibold ${section === "exams" ? "bg-slate-100 text-slate-900" : "text-slate-500"}`}>AP / IB credit ({transcript.examCredits.length})</button></div>
    <div className="overflow-y-auto p-5 sm:p-6">
      {section === "courses" ? <div className="space-y-3">
        {transcript.courses.map((course) => <article key={course.id} className="grid gap-3 rounded-2xl border border-slate-200 p-3 sm:grid-cols-[110px_1fr_90px_80px_120px_36px] sm:items-end">
          <label><span className="field-label">Course</span><input aria-label={`Course code ${course.id}`} className="field !px-2" value={course.code} onChange={(event) => updateCourse(course.id, { code: event.target.value })} /></label>
          <label><span className="field-label">Title</span><input aria-label={`Course title ${course.id}`} className="field !px-2" value={course.title} onChange={(event) => updateCourse(course.id, { title: event.target.value })} /></label>
          <label><span className="field-label">Grade</span><select aria-label={`Grade ${course.code}`} className="field !px-2" value={course.grade} onChange={(event) => updateCourse(course.id, { grade: event.target.value })}>{gradeOptions.map((grade) => <option key={grade}>{grade}</option>)}</select></label>
          <label><span className="field-label">Credits</span><input aria-label={`Credits ${course.code}`} type="number" min={0} max={20} className="field !px-2" value={course.creditsAttempted} onChange={(event) => updateCourse(course.id, { creditsAttempted: Number(event.target.value) })} /></label>
          <label><span className="field-label">Status</span><select aria-label={`Status ${course.code}`} className="field !px-2" value={course.status} onChange={(event) => updateCourse(course.id, { status: event.target.value as CourseStatus })}><option value="completed">Completed</option><option value="in-progress">In progress</option><option value="planned">Planned</option></select></label>
          <button onClick={() => removeCourse(course.id)} aria-label={`Remove ${course.code}`} className="mb-1 grid size-9 place-items-center rounded-xl text-slate-400 hover:bg-rose-50 hover:text-rose-600"><Trash2 className="size-4" /></button>
        </article>)}
        <button onClick={addCourse} className="secondary-button"><Plus className="size-4" /> Add college course</button>
      </div> : <div className="space-y-3">
        {transcript.examCredits.map((exam) => <article key={exam.id} className="grid gap-3 rounded-2xl border border-slate-200 p-4 sm:grid-cols-[90px_1fr_90px_110px_80px_36px] sm:items-end">
          <label><span className="field-label">Type</span><select aria-label={`Exam type ${exam.id}`} className="field !px-2" value={exam.type} onChange={(event) => updateExam(exam.id, { type: event.target.value as ExamCredit["type"] })}><option>AP</option><option>IB</option><option>CLEP</option><option>Other</option></select></label>
          <label><span className="field-label">Subject</span><input aria-label={`Exam subject ${exam.id}`} className="field !px-2" value={exam.subject} onChange={(event) => updateExam(exam.id, { subject: event.target.value })} /></label>
          <label><span className="field-label">Score</span><input aria-label={`Exam score ${exam.id}`} className="field !px-2" value={exam.score} onChange={(event) => updateExam(exam.id, { score: event.target.value })} /></label>
          <label><span className="field-label">Credits</span><input aria-label={`Exam credits ${exam.id}`} type="number" min={0} max={45} className="field !px-2" value={exam.creditsAwarded} onChange={(event) => updateExam(exam.id, { creditsAwarded: Number(event.target.value) })} /></label>
          <button onClick={() => updateExam(exam.id, { enabled: !exam.enabled })} className={`mb-1 rounded-xl border px-3 py-2 text-xs font-semibold ${exam.enabled ? "border-teal-300 bg-teal-50 text-teal-700" : "border-slate-200 text-slate-500"}`}>{exam.enabled ? "Applied" : "Ignored"}</button>
          <button onClick={() => setTranscript({ ...transcript, examCredits: transcript.examCredits.filter((item) => item.id !== exam.id) })} aria-label={`Remove ${exam.subject}`} className="mb-1 grid size-9 place-items-center rounded-xl text-slate-400 hover:bg-rose-50 hover:text-rose-600"><Trash2 className="size-4" /></button>
        </article>)}
        <button onClick={addExam} className="secondary-button"><Plus className="size-4" /> Add AP credit</button>
      </div>}
    </div>
    <footer className="flex shrink-0 items-center justify-between border-t border-slate-200 px-5 py-4"><p className="text-xs text-slate-500">Changes recalculate the scenario automatically.</p><button onClick={onClose} className="primary-button">Done</button></footer>
  </ModalFrame>;
}

export function CustomCoursePanel({ terms, onAdd, onClose }: { terms: SimulatorTerm[]; onAdd: (course: PlannedCourse) => void; onClose: () => void }) {
  const [code, setCode] = useState("BIO& 160");
  const [title, setTitle] = useState("General Biology");
  const [credits, setCredits] = useState(5);
  const [termId, setTermId] = useState(terms[0]?.id ?? "fall-2026");
  const term = terms.find((item) => item.id === termId) ?? terms[0];
  const submit = () => {
    if (!code.trim() || !title.trim() || !term) return;
    onAdd({ id: `custom-${Date.now()}`, course: code.trim().toUpperCase(), title: title.trim(), credits, termId: term.id, termLabel: term.label, satisfies: ["Custom plan course"], source: "custom" });
    onClose();
  };
  return <ModalFrame title="Add a course to the plan" description="Use this for a course that is not already in the recommendation library." onClose={onClose}>
    <div className="grid gap-4 p-5 sm:grid-cols-2 sm:p-6">
      <label><span className="field-label">Course code</span><input aria-label="Custom course code" className="field" value={code} onChange={(event) => setCode(event.target.value)} /></label>
      <label><span className="field-label">Credits</span><input aria-label="Custom course credits" type="number" min={1} max={20} className="field" value={credits} onChange={(event) => setCredits(Number(event.target.value))} /></label>
      <label className="sm:col-span-2"><span className="field-label">Course title</span><input aria-label="Custom course title" className="field" value={title} onChange={(event) => setTitle(event.target.value)} /></label>
      <label className="sm:col-span-2"><span className="field-label">Quarter</span><select aria-label="Custom course quarter" className="field" value={termId} onChange={(event) => setTermId(event.target.value)}>{terms.map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}</select></label>
    </div>
    <footer className="flex shrink-0 justify-end gap-2 border-t border-slate-200 px-5 py-4"><button onClick={onClose} className="secondary-button">Cancel</button><button onClick={submit} className="primary-button">Add to plan</button></footer>
  </ModalFrame>;
}

export function SimulationSummaryPanel({ summary, updating }: { summary: SimulationSummary; updating: boolean }) {
  const metrics = [
    { label: "Transfer eligible", value: `${summary.transferEligiblePrograms}/${summary.totalPrograms}`, detail: "selected programs" },
    { label: "Major eligible", value: `${summary.majorEligiblePrograms}/${summary.totalPrograms}`, detail: "ready or nearly ready" },
    { label: "Transferable credits", value: summary.projectedTransferableCredits.toString(), detail: `${summary.plannedCredits} planned` },
    { label: "Graduation estimate", value: summary.estimatedGraduationTerm, detail: `${summary.termsRemaining} terms remaining` },
    { label: "Missing prerequisites", value: summary.missingPrerequisiteCount.toString(), detail: "across selected paths" },
    { label: "General education", value: `${summary.generalEducationPercent}%`, detail: "estimated progress" },
    { label: "Remaining credits", value: summary.estimatedRemainingCredits.toString(), detail: "to sample 180-credit degree" },
    { label: "Options open", value: `${summary.openOptionIds.length}/${summary.totalPrograms}`, detail: `projected GPA ${summary.projectedGpa.toFixed(2)}` },
  ];
  return <section data-testid="simulator-summary" className="relative mt-8 overflow-visible rounded-[var(--radius-card)] border border-[var(--border)] shadow-[var(--shadow-card)]" style={{ background: "var(--gradient-hope)" }}>
    {/* eslint-disable-next-line @next/next/no-img-element */}
    <img src="/pathly/pet/pip-mini-pet.png" alt="" width={76} className="absolute -top-[42px] right-[26px] hidden lg:block" />
    <div className="flex flex-col gap-2 border-b border-[var(--border)] px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-2"><TrendingUp className="size-4 text-[var(--path-green)]" /><h2 className="text-sm font-bold text-[var(--forest)]">Live scenario impact</h2><span className={`size-2 rounded-full ${updating ? "animate-pulse bg-[var(--butter)]" : "bg-[var(--path-green)]"}`} /></div>
      <p className="text-[10px] text-slate-400">Sample calculations update after every change</p>
    </div>
    <div className="grid grid-cols-2 lg:grid-cols-4">{metrics.map((metric) => <div key={metric.label} className="min-h-24 p-4"><p className="text-[10px] font-bold uppercase tracking-wide text-slate-500">{metric.label}</p><p className="mt-2 text-2xl font-bold tracking-tight text-[var(--forest)]" style={{ fontFamily: "var(--font-heading)" }}>{metric.value}</p><p className="mt-1 text-[10px] text-slate-500">{metric.detail}</p></div>)}</div>
    {summary.overloadedTermIds.length > 0 && <div className="flex items-center gap-2 border-t border-amber-200 bg-amber-50 px-4 py-3 text-xs text-amber-800"><AlertTriangle className="size-4" />One or more quarters exceed the selected maximum credit load.</div>}
    <div className={`flex items-center gap-2 border-t px-4 py-3 text-xs ${summary.onTrackForGraduationTarget ? "border-emerald-100 bg-emerald-50 text-emerald-800" : "border-amber-200 bg-amber-50 text-amber-800"}`}><GraduationCap className="size-4" />{summary.onTrackForGraduationTarget ? `On track for the ${summary.graduationTarget} target in this sample scenario.` : `Current estimate is later than the ${summary.graduationTarget} target.`}</div>
  </section>;
}

export function ComparisonView({ plans, onSave, onRestore, onDelete }: { plans: PlanComparison[]; onSave: () => void; onRestore: (plan: PlanComparison) => void; onDelete: (id: string) => void }) {
  const baseline = plans[0]?.summary;
  return <section>
    <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"><div className="max-w-2xl"><p className="text-xs font-bold uppercase tracking-[0.15em] text-teal-700">Compare plans</p><h1 className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-slate-900">See which scenario preserves more options.</h1><p className="mt-2 text-sm text-slate-500">Save the current plan, change any inputs, then save again for a side-by-side comparison.</p></div><button onClick={onSave} className="primary-button"><GitCompareArrows className="size-4" /> Save current plan</button></div>
    {plans.length === 0 ? <div className="mt-6 rounded-3xl border border-dashed border-slate-300 bg-white p-12 text-center"><BookOpenCheck className="mx-auto size-8 text-slate-300" /><h2 className="mt-4 font-semibold text-slate-900">No saved plans yet</h2><p className="mt-2 text-sm text-slate-500">Save this version, adjust the simulator, and save another.</p></div> : <div className="mt-6 grid gap-4 xl:grid-cols-3">{plans.map((plan, index) => {
      const schools = plan.targets.map((target) => getSchool(target.schoolId)?.shortName).filter(Boolean).join(", ");
      const majors = plan.targets.flatMap((target) => target.majorIds).map((id) => getMajor(id)?.name).filter(Boolean);
      const creditDelta = baseline ? Math.round((plan.summary.projectedTransferableCredits - baseline.projectedTransferableCredits) * 10) / 10 : 0;
      return <article key={plan.id} className={`card overflow-hidden ${index === 0 ? "ring-1 ring-teal-300" : ""}`}>
        <div className="border-b border-slate-100 p-5"><div className="flex items-start justify-between gap-3"><div><p className="text-[10px] font-bold uppercase tracking-wide text-teal-700">{index === 0 ? "Baseline" : `Scenario ${index + 1}`}</p><h2 className="mt-1 font-semibold text-slate-900">{plan.label}</h2></div><button onClick={() => onDelete(plan.id)} aria-label={`Delete ${plan.label}`} className="rounded-lg p-1.5 text-slate-400 hover:bg-rose-50 hover:text-rose-600"><Trash2 className="size-4" /></button></div><p className="mt-2 text-xs text-slate-500">{schools}</p><p className="mt-1 line-clamp-2 text-[10px] text-slate-400">{majors.join(" · ")}</p></div>
        <div className="grid grid-cols-2 gap-px bg-slate-100">{[
          ["Transfer eligible", `${plan.summary.transferEligiblePrograms}/${plan.summary.totalPrograms}`],
          ["Major eligible", `${plan.summary.majorEligiblePrograms}/${plan.summary.totalPrograms}`],
          ["Transfer credits", `${plan.summary.projectedTransferableCredits}${index > 0 && creditDelta !== 0 ? ` (${creditDelta > 0 ? "+" : ""}${creditDelta})` : ""}`],
          ["GE progress", `${plan.summary.generalEducationPercent}%`],
          ["Graduation", plan.summary.estimatedGraduationTerm],
          ["Options open", `${plan.summary.openOptionIds.length}/${plan.summary.totalPrograms}`],
        ].map(([label, value]) => <div key={label} className="bg-white p-3"><p className="text-[9px] uppercase tracking-wide text-slate-400">{label}</p><p className="mt-1 text-sm font-semibold text-slate-800">{value}</p></div>)}</div>
        <div className="p-4"><p className="text-[10px] text-slate-500">{plan.scenario.currentInstitution} · {plan.scenario.preferredCreditLoad} credit max · target {plan.scenario.graduationTarget}</p><button onClick={() => onRestore(plan)} className="secondary-button mt-3 w-full"><RotateCcw className="size-3.5" /> Restore this plan</button></div>
      </article>;
    })}</div>}
    {plans.length === 1 && <p className="mt-4 text-xs text-slate-500">Change a setting, course, grade, school, or major and save again to compare.</p>}
  </section>;
}
