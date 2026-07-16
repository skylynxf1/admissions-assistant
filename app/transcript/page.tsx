"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { AlertCircle, ArrowRight, CheckCircle2, FileText, LoaderCircle, PencilLine, Plus, Trash2, UploadCloud } from "lucide-react";
import { useApp } from "@/components/app-provider";
import { ConfidenceBadge, EmptyState, SampleDataBanner } from "@/components/ui";
import { academicPlanningServices } from "@/lib/services";
import type { CourseRecord } from "@/lib/types";

export default function TranscriptPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { transcript, setTranscript } = useApp();
  const [inputMode, setInputMode] = useState<"pdf" | "manual">("pdf");
  const [status, setStatus] = useState<"idle" | "extracting" | "ready" | "error">(transcript.courses.length ? "ready" : "idle");
  const [error, setError] = useState("");

  const extractFile = async (file?: File) => {
    if (file && file.type !== "application/pdf") {
      setError("Please choose a PDF transcript.");
      setStatus("error");
      return;
    }
    setError("");
    setStatus("extracting");
    setTranscript({ ...transcript, extractionStatus: "extracting", fileName: file?.name ?? "sample-transfer-transcript.pdf" });
    await new Promise((resolve) => window.setTimeout(resolve, 650));
    try {
      const parsed = await academicPlanningServices.transcriptParser.parse(file?.name);
      setTranscript(parsed);
      setStatus("ready");
    } catch {
      setError("The demo parser could not load the sample transcript. Try manual input.");
      setStatus("error");
    }
  };

  const updateCourse = (id: string, patch: Partial<CourseRecord>) => {
    setTranscript({ ...transcript, verificationStatus: "reviewing", courses: transcript.courses.map((course) => course.id === id ? { ...course, ...patch } : course) });
  };

  const addCourse = () => {
    const course: CourseRecord = {
      id: `manual-${Date.now()}`, institution: transcript.institutions[0] ?? "", code: "", title: "", term: "Fall 2026",
      creditsAttempted: 5, creditsEarned: 0, grade: "IP", status: "planned", confidence: "high", repeat: false, transfer: false,
    };
    setTranscript({ ...transcript, verificationStatus: "reviewing", courses: [...transcript.courses, course] });
    setStatus("ready");
  };

  const startManual = () => {
    setInputMode("manual");
    setTranscript({ ...transcript, fileName: undefined, courses: [], institutions: [transcript.institutions[0] ?? ""], extractionStatus: "complete", verificationStatus: "reviewing" });
    setStatus("idle");
  };

  const continueToTargets = () => {
    setTranscript({ ...transcript, verificationStatus: "confirmed" });
    router.push("/targets");
  };

  const earned = transcript.courses.filter((course) => course.status === "completed").reduce((sum, course) => sum + course.creditsEarned, 0);
  const uncertain = transcript.courses.filter((course) => course.confidence !== "high").length;

  return (
    <main className="mx-auto max-w-[1280px] px-5 py-10 lg:px-8 lg:py-12">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
        <div><p className="text-xs font-bold uppercase tracking-[0.16em] text-teal-700">Your academic record</p><h1 className="mt-2 text-3xl font-semibold tracking-[-0.045em] text-[var(--ink)]">Upload, then verify every detail.</h1><p className="mt-2 max-w-2xl text-slate-600">Nothing is locked. Correct course codes, grades, credits, or confidence before analysis.</p></div>
        <div className="flex rounded-xl border border-slate-200 bg-white p-1">
          <button onClick={() => setInputMode("pdf")} className={`rounded-lg px-3 py-2 text-sm font-semibold ${inputMode === "pdf" ? "bg-[var(--ink)] text-white" : "text-slate-500"}`}>PDF upload</button>
          <button onClick={startManual} className={`rounded-lg px-3 py-2 text-sm font-semibold ${inputMode === "manual" ? "bg-[var(--ink)] text-white" : "text-slate-500"}`}>Manual input</button>
        </div>
      </div>

      <div className="mt-7 grid gap-5 lg:grid-cols-[minmax(0,1fr)_260px]">
        <section className="space-y-5">
          {inputMode === "pdf" && (
            <div className="card p-5">
              <input ref={fileInputRef} type="file" accept="application/pdf" className="hidden" onChange={(event) => void extractFile(event.target.files?.[0])} />
              {status === "extracting" ? (
                <div className="flex min-h-44 flex-col items-center justify-center rounded-2xl border border-teal-200 bg-teal-50/60 text-center">
                  <LoaderCircle className="size-7 animate-spin text-teal-600" /><p className="mt-3 font-semibold text-teal-950">Extracting a sample academic record…</p><p className="mt-1 text-sm text-teal-700">In production, GPT-5.6 will return structured fields with page-level confidence.</p>
                </div>
              ) : (
                <div className="flex min-h-44 flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-5 text-center">
                  <div className="grid size-11 place-items-center rounded-xl bg-white text-teal-700 shadow-sm"><UploadCloud className="size-5" /></div>
                  <p className="mt-3 font-semibold text-slate-900">Upload a PDF of your transcript</p><p className="mt-1 text-sm text-slate-500">Official or unofficial · PDF only · demo uses fictional extraction</p>
                  <div className="mt-4 flex flex-wrap justify-center gap-2"><button onClick={() => fileInputRef.current?.click()} className="primary-button">Choose PDF</button><button onClick={() => void extractFile()} className="secondary-button">Use demo transcript</button></div>
                </div>
              )}
              {status === "error" && <div className="mt-3 flex items-center gap-2 rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-700"><AlertCircle className="size-4" />{error}</div>}
              {transcript.fileName && status === "ready" && <div className="mt-3 flex items-center justify-between rounded-xl border border-slate-200 px-3 py-2.5"><div className="flex items-center gap-2.5"><FileText className="size-4 text-teal-600" /><div><p className="text-sm font-medium text-slate-800">{transcript.fileName}</p><p className="text-xs text-slate-400">Sample extraction complete · review required</p></div></div><CheckCircle2 className="size-5 text-emerald-500" /></div>}
            </div>
          )}

          <div className="card overflow-hidden">
            <div className="flex flex-col justify-between gap-3 border-b border-slate-200 px-5 py-4 sm:flex-row sm:items-center">
              <div><div className="flex items-center gap-2"><PencilLine className="size-4 text-teal-600" /><h2 className="font-semibold text-slate-900">Transcript review</h2></div><p className="mt-1 text-xs text-slate-500">{transcript.courses.length} records · {uncertain} need extra attention</p></div>
              <button onClick={addCourse} className="secondary-button !min-h-9 !px-3 !py-1.5"><Plus className="size-3.5" /> Add course</button>
            </div>
            {transcript.courses.length === 0 ? <div className="p-5"><EmptyState title="No courses yet" description="Add your first course manually, or switch to PDF upload and use the demo transcript." /></div> : (
              <div className="desktop-table">
                <table className="w-full min-w-[980px] border-collapse text-left">
                  <thead className="bg-slate-50 text-[11px] font-semibold uppercase tracking-wide text-slate-500"><tr><th className="px-4 py-3">Institution</th><th className="px-3 py-3">Course</th><th className="px-3 py-3">Title</th><th className="px-3 py-3">Term</th><th className="px-3 py-3">Credits</th><th className="px-3 py-3">Grade</th><th className="px-3 py-3">Status</th><th className="px-3 py-3">Confidence</th><th className="px-3 py-3" /></tr></thead>
                  <tbody className="divide-y divide-slate-100">
                    {transcript.courses.map((course) => (
                      <tr key={course.id} className="group hover:bg-teal-50/30">
                        <td className="px-4 py-2"><input value={course.institution} onChange={(event) => updateCourse(course.id, { institution: event.target.value })} className="w-36 bg-transparent text-xs text-slate-600 outline-none focus:text-slate-900" /></td>
                        <td className="px-3 py-2"><input value={course.code} onChange={(event) => updateCourse(course.id, { code: event.target.value })} className="w-24 rounded-lg border border-transparent bg-transparent px-2 py-1.5 text-sm font-semibold text-slate-900 outline-none focus:border-teal-300 focus:bg-white" /></td>
                        <td className="px-3 py-2"><input value={course.title} onChange={(event) => updateCourse(course.id, { title: event.target.value })} className="w-40 rounded-lg border border-transparent bg-transparent px-2 py-1.5 text-sm text-slate-700 outline-none focus:border-teal-300 focus:bg-white" /></td>
                        <td className="px-3 py-2"><input value={course.term} onChange={(event) => updateCourse(course.id, { term: event.target.value })} className="w-24 bg-transparent text-xs text-slate-600 outline-none" /></td>
                        <td className="px-3 py-2"><input type="number" min="0" step="0.5" value={course.creditsAttempted} onChange={(event) => updateCourse(course.id, { creditsAttempted: Number(event.target.value), creditsEarned: course.status === "completed" ? Number(event.target.value) : course.creditsEarned })} className="w-14 rounded-lg border border-slate-200 px-2 py-1.5 text-sm outline-none focus:border-teal-400" /></td>
                        <td className="px-3 py-2"><input value={course.grade} onChange={(event) => updateCourse(course.id, { grade: event.target.value })} className="w-12 rounded-lg border border-slate-200 px-2 py-1.5 text-sm outline-none focus:border-teal-400" /></td>
                        <td className="px-3 py-2"><select value={course.status} onChange={(event) => updateCourse(course.id, { status: event.target.value as CourseRecord["status"] })} className="rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-xs text-slate-600"><option value="completed">Completed</option><option value="in-progress">In progress</option><option value="planned">Planned</option></select></td>
                        <td className="px-3 py-2"><div className="flex items-center gap-2"><ConfidenceBadge level={course.confidence} /><select aria-label={`Confidence for ${course.code}`} value={course.confidence} onChange={(event) => updateCourse(course.id, { confidence: event.target.value as CourseRecord["confidence"] })} className="w-5 opacity-0 transition group-hover:opacity-100"><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option></select></div></td>
                        <td className="px-3 py-2"><button aria-label={`Delete ${course.code}`} onClick={() => setTranscript({ ...transcript, courses: transcript.courses.filter((item) => item.id !== course.id) })} className="rounded-lg p-2 text-slate-300 hover:bg-rose-50 hover:text-rose-500"><Trash2 className="size-4" /></button></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {transcript.examCredits.length > 0 && (
            <div className="card p-5"><div className="flex items-center justify-between gap-4"><div><h2 className="font-semibold text-slate-900">Exam credit</h2><p className="mt-1 text-xs text-slate-500">Applicability will be evaluated separately for each target program.</p></div><span className="rounded-full bg-violet-50 px-2.5 py-1 text-xs font-semibold text-violet-700">{transcript.examCredits.length} record</span></div>
              {transcript.examCredits.map((credit) => <div key={credit.id} className="mt-4 grid gap-3 rounded-xl bg-slate-50 p-3 sm:grid-cols-[80px_1fr_80px_100px]"><select value={credit.type} onChange={(event) => setTranscript({ ...transcript, examCredits: transcript.examCredits.map((item) => item.id === credit.id ? { ...item, type: event.target.value as typeof credit.type } : item) })} className="field !py-2"><option>AP</option><option>IB</option><option>CLEP</option><option>Other</option></select><input value={credit.subject} onChange={(event) => setTranscript({ ...transcript, examCredits: transcript.examCredits.map((item) => item.id === credit.id ? { ...item, subject: event.target.value } : item) })} className="field !py-2" /><input aria-label="Exam score" value={credit.score} onChange={(event) => setTranscript({ ...transcript, examCredits: transcript.examCredits.map((item) => item.id === credit.id ? { ...item, score: event.target.value } : item) })} className="field !py-2" /><div className="field !py-2 text-center text-sm text-slate-600">{credit.creditsAwarded} est. cr.</div></div>)}
            </div>
          )}

          <div className="flex flex-col-reverse justify-between gap-3 sm:flex-row sm:items-center"><button onClick={() => router.push("/onboarding")} className="secondary-button">Back</button><button onClick={continueToTargets} disabled={transcript.courses.length === 0} className="primary-button">Confirm transcript & continue <ArrowRight className="size-4" /></button></div>
        </section>

        <aside className="space-y-4">
          <div className="card p-5"><p className="text-xs font-bold uppercase tracking-[0.14em] text-slate-400">Record snapshot</p><div className="mt-4 grid grid-cols-2 gap-3 lg:grid-cols-1">
            {[['Credits earned', earned.toString()], ['Current GPA', transcript.cumulativeGpa.toFixed(2)], ['Institutions', transcript.institutions.length.toString()], ['In progress', transcript.courses.filter((course) => course.status === "in-progress").reduce((sum, course) => sum + course.creditsAttempted, 0).toString()]].map(([label, value]) => <div key={label} className="rounded-xl bg-slate-50 p-3"><p className="text-[11px] text-slate-500">{label}</p><p className="mt-1 text-xl font-semibold tracking-tight text-[var(--ink)]">{value}</p></div>)}
          </div></div>
          <div className="card p-5"><h3 className="text-sm font-semibold text-slate-900">Review checklist</h3><div className="mt-3 space-y-2 text-xs text-slate-600">{["Institution names", "Course codes and titles", "Attempted and earned credits", "Grades and course status", "Low-confidence records"].map((item) => <div key={item} className="flex items-center gap-2"><CheckCircle2 className="size-3.5 text-teal-600" />{item}</div>)}</div></div>
          <SampleDataBanner compact />
        </aside>
      </div>
    </main>
  );
}
