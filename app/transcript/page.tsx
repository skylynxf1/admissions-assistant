"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Check, FileText, LoaderCircle, Pencil, Plus, Trash2, UploadCloud } from "lucide-react";
import { useApp } from "@/components/app-provider";
import { academicPlanningServices } from "@/lib/services";
import type { CourseRecord } from "@/lib/types";

type InputChoice = "pdf" | "manual" | null;

export default function TranscriptPage() {
  const router = useRouter();
  const fileInput = useRef<HTMLInputElement>(null);
  const { transcript, setTranscript } = useApp();
  const [choice, setChoice] = useState<InputChoice>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const loadPdf = async (file?: File) => {
    if (file && file.type !== "application/pdf") {
      setError("Please choose a PDF file.");
      return;
    }
    setChoice("pdf");
    setLoading(true);
    setError("");
    try {
      await new Promise((resolve) => window.setTimeout(resolve, 550));
      const parsed = await academicPlanningServices.transcriptParser.parse(file?.name);
      setTranscript({ ...parsed, verificationStatus: "reviewing" });
    } catch {
      setError("We couldn’t read that file. Try manual entry instead.");
      setChoice(null);
    } finally {
      setLoading(false);
    }
  };

  const startManual = () => {
    setChoice("manual");
    setTranscript({
      ...transcript,
      fileName: undefined,
      courses: [],
      institutions: [transcript.institutions[0] || ""],
      extractionStatus: "complete",
      verificationStatus: "reviewing",
    });
  };

  const updateCourse = (id: string, patch: Partial<CourseRecord>) => {
    setTranscript({
      ...transcript,
      verificationStatus: "reviewing",
      courses: transcript.courses.map((course) => course.id === id ? { ...course, ...patch } : course),
    });
  };

  const addCourse = () => {
    const course: CourseRecord = {
      id: `manual-${Date.now()}`,
      institution: transcript.institutions[0] || "",
      code: "",
      title: "",
      term: "Fall 2026",
      creditsAttempted: 5,
      creditsEarned: 0,
      grade: "IP",
      status: "planned",
      confidence: "high",
      repeat: false,
      transfer: false,
    };
    setTranscript({ ...transcript, courses: [...transcript.courses, course] });
  };

  const continueFlow = () => {
    setTranscript({ ...transcript, verificationStatus: "confirmed" });
    router.push("/targets");
  };

  if (!choice) {
    return (
      <main className="mx-auto flex min-h-[calc(100vh-130px)] max-w-3xl items-center px-5 py-12">
        <section className="w-full text-center">
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-teal-700">Your transcript</p>
          <h1 className="mt-3 text-3xl font-semibold tracking-[-0.045em] text-[var(--ink)] sm:text-4xl">Add your academic record.</h1>
          <p className="mx-auto mt-3 max-w-xl text-slate-500">We’ll turn it into an editable course list. You review everything before it affects your plan.</p>

          <input ref={fileInput} type="file" accept="application/pdf" className="hidden" onChange={(event) => void loadPdf(event.target.files?.[0])} />
          <div className="card mx-auto mt-8 max-w-xl p-5 sm:p-7">
            <button onClick={() => fileInput.current?.click()} className="group flex w-full flex-col items-center rounded-2xl border-2 border-dashed border-teal-200 bg-teal-50/40 px-6 py-12 transition hover:border-teal-400 hover:bg-teal-50">
              <span className="grid size-14 place-items-center rounded-2xl bg-white text-teal-700 shadow-sm transition group-hover:-translate-y-0.5"><UploadCloud className="size-6" /></span>
              <span className="mt-4 text-base font-semibold text-slate-900">Upload PDF transcript</span>
              <span className="mt-1 text-sm text-slate-500">Official or unofficial · PDF only</span>
            </button>
            <button onClick={() => void loadPdf()} className="mt-3 text-xs font-semibold text-teal-700 hover:underline">Or try the sample PDF</button>
            <div className="my-6 flex items-center gap-3"><span className="h-px flex-1 bg-slate-200" /><span className="text-xs font-medium text-slate-400">or</span><span className="h-px flex-1 bg-slate-200" /></div>
            <button onClick={startManual} className="secondary-button w-full"><Pencil className="size-4" /> Enter courses manually</button>
            {error && <p className="mt-4 text-sm text-rose-600">{error}</p>}
          </div>
        </section>
      </main>
    );
  }

  if (loading) {
    return (
      <main className="mx-auto flex min-h-[calc(100vh-130px)] max-w-2xl items-center justify-center px-5 text-center">
        <div><LoaderCircle className="mx-auto size-8 animate-spin text-teal-600" /><h1 className="mt-4 text-xl font-semibold text-slate-900">Reading your transcript…</h1><p className="mt-2 text-sm text-slate-500">Creating an editable review. Nothing is final yet.</p></div>
      </main>
    );
  }

  const earned = transcript.courses.filter((course) => course.status === "completed").reduce((sum, course) => sum + course.creditsEarned, 0);

  return (
    <main className="mx-auto max-w-6xl px-5 py-10 lg:px-8 lg:py-12">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-teal-700"><Check className="size-3.5" /> {choice === "pdf" ? "PDF added" : "Manual entry"}</div>
          <h1 className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-[var(--ink)]">Review your courses.</h1>
          <p className="mt-2 text-sm text-slate-500">Edit anything that doesn’t look right.</p>
        </div>
        <div className="flex gap-2"><button onClick={() => setChoice(null)} className="secondary-button">Start over</button><button onClick={addCourse} className="secondary-button"><Plus className="size-4" /> Add course</button></div>
      </div>

      {choice === "pdf" && transcript.fileName && (
        <div className="mt-6 flex items-center gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm"><FileText className="size-4 text-teal-600" /><span className="font-medium text-slate-800">{transcript.fileName}</span><span className="ml-auto text-xs text-slate-400">Sample extraction · editable</span></div>
      )}

      <section className="card mt-4 overflow-hidden">
        {transcript.courses.length === 0 ? (
          <div className="flex min-h-72 flex-col items-center justify-center px-5 text-center"><div className="grid size-12 place-items-center rounded-2xl bg-slate-100 text-slate-400"><Pencil className="size-5" /></div><h2 className="mt-4 font-semibold text-slate-900">Add your first course</h2><p className="mt-1 text-sm text-slate-500">Course code, title, credits, and grade are enough to start.</p><button onClick={addCourse} className="primary-button mt-5"><Plus className="size-4" /> Add course</button></div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[840px] text-left">
              <thead className="border-b border-slate-200 bg-slate-50 text-[11px] font-semibold uppercase tracking-wide text-slate-400"><tr><th className="px-4 py-3">Course</th><th className="px-3 py-3">Title</th><th className="px-3 py-3">Term</th><th className="px-3 py-3">Credits</th><th className="px-3 py-3">Grade</th><th className="px-3 py-3">Status</th><th className="w-12" /></tr></thead>
              <tbody className="divide-y divide-slate-100">
                {transcript.courses.map((course) => (
                  <tr key={course.id} className="hover:bg-teal-50/30">
                    <td className="px-4 py-2.5"><input aria-label={`Course code ${course.id}`} value={course.code} onChange={(event) => updateCourse(course.id, { code: event.target.value })} className="w-28 rounded-lg border border-transparent bg-transparent px-2 py-2 text-sm font-semibold outline-none focus:border-teal-300 focus:bg-white" /></td>
                    <td className="px-3 py-2.5"><input aria-label={`Course title ${course.id}`} value={course.title} onChange={(event) => updateCourse(course.id, { title: event.target.value })} className="w-52 rounded-lg border border-transparent bg-transparent px-2 py-2 text-sm outline-none focus:border-teal-300 focus:bg-white" /></td>
                    <td className="px-3 py-2.5"><input aria-label={`Course term ${course.id}`} value={course.term} onChange={(event) => updateCourse(course.id, { term: event.target.value })} className="w-28 rounded-lg border border-transparent bg-transparent px-2 py-2 text-sm text-slate-600 outline-none focus:border-teal-300 focus:bg-white" /></td>
                    <td className="px-3 py-2.5"><input aria-label={`Credits ${course.id}`} type="number" min="0" step="0.5" value={course.creditsAttempted} onChange={(event) => updateCourse(course.id, { creditsAttempted: Number(event.target.value), creditsEarned: course.status === "completed" ? Number(event.target.value) : 0 })} className="w-16 rounded-lg border border-slate-200 px-2 py-2 text-sm outline-none focus:border-teal-400" /></td>
                    <td className="px-3 py-2.5"><input aria-label={`Grade ${course.id}`} value={course.grade} onChange={(event) => updateCourse(course.id, { grade: event.target.value })} className="w-14 rounded-lg border border-slate-200 px-2 py-2 text-sm outline-none focus:border-teal-400" /></td>
                    <td className="px-3 py-2.5"><select aria-label={`Status ${course.id}`} value={course.status} onChange={(event) => updateCourse(course.id, { status: event.target.value as CourseRecord["status"] })} className="rounded-lg border border-slate-200 bg-white px-2 py-2 text-xs"><option value="completed">Completed</option><option value="in-progress">In progress</option><option value="planned">Planned</option></select></td>
                    <td className="pr-3"><button aria-label={`Delete ${course.code || "course"}`} onClick={() => setTranscript({ ...transcript, courses: transcript.courses.filter((item) => item.id !== course.id) })} className="rounded-lg p-2 text-slate-300 hover:bg-rose-50 hover:text-rose-500"><Trash2 className="size-4" /></button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <div className="mt-5 flex flex-col gap-3 rounded-2xl bg-[var(--ink)] p-4 text-white sm:flex-row sm:items-center sm:justify-between">
        <div><p className="text-sm font-semibold">{transcript.courses.length} courses · {earned} earned credits</p><p className="mt-0.5 text-xs text-slate-300">You can edit this again from the planner.</p></div>
        <button disabled={transcript.courses.length === 0} onClick={continueFlow} className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-[var(--lime)] px-4 text-sm font-semibold text-[var(--ink)] disabled:opacity-50">Looks right — choose schools <ArrowRight className="size-4" /></button>
      </div>
    </main>
  );
}
