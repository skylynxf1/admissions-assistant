"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  AlertTriangle, ArrowRight, Check, ChevronDown, ChevronUp, FileSearch, FileText,
  LoaderCircle, Pencil, Plus, RefreshCw, ShieldCheck, Trash2, UploadCloud, X,
} from "lucide-react";
import { useApp } from "@/components/app-provider";
import { getSupabaseBrowserClient } from "@/lib/supabase/client";
import type { CourseRecord, ExamCredit, TranscriptData } from "@/lib/types";
import type { TranscriptPipelineResult, TranscriptWarningSeverity, TranscriptWarningState } from "@/lib/transcript/types";

type InputChoice = "pdf" | "manual" | null;
type ProgressStage = "uploading" | "parsing" | "extracting" | "validating" | "review";

interface ReviewWarning {
  id: string;
  sourceDocumentId?: string;
  code: string;
  severity: TranscriptWarningSeverity;
  state: TranscriptWarningState;
  message: string;
  entityId: string | null;
  pageNumber: number | null;
}

interface UploadedDocumentView {
  id: string;
  fileName: string;
  status: "needs_review" | "completed";
  mode: "supabase" | "sample";
}

interface DetailedTranscript {
  document: { id: string; original_filename: string };
  institutions: Array<{ id: string; institution_name: string }>;
  terms: Array<{ id: string; student_institution_id: string; label: string }>;
  courses: Array<{
    id: string; student_institution_id: string; academic_term_id: string; course_code: string; course_title: string;
    credits_attempted: number | null; credits_earned: number | null; grade: string | null; course_status: string;
    repeat_indicator: boolean; transfer_indicator: boolean; extraction_confidence: number; source_page: number; source_raw_text: string | null;
  }>;
  examCredits: Array<{ id: string; exam_type: string; subject: string; score: string | null; credits_awarded: number | null; extraction_confidence: number; source_page: number }>;
  summary: { cumulative_gpa: number | null } | null;
  warnings: Array<{ id: string; warning_code: string; severity: TranscriptWarningSeverity; state: TranscriptWarningState; message: string; entity_source_id: string | null; source_page: number | null }>;
}

const progressCopy: Record<ProgressStage, string> = {
  uploading: "Uploading privately",
  parsing: "Reading pages and tables",
  extracting: "Building course records",
  validating: "Checking totals and confidence",
  review: "Preparing your review",
};

function confidenceLabel(value?: number) {
  if (value === undefined) return null;
  return value >= 0.9 ? "High" : value >= 0.75 ? "Medium" : "Low";
}

function detailToPlannerData(detail: DetailedTranscript): TranscriptData {
  const institutions = new Map(detail.institutions.map((item) => [item.id, item.institution_name]));
  const terms = new Map(detail.terms.map((item) => [item.id, item.label]));
  return {
    id: detail.document.id,
    fileName: detail.document.original_filename,
    institutions: detail.institutions.map((item) => item.institution_name),
    courses: detail.courses.map((course) => ({
      id: course.id,
      normalizedRecordId: course.id,
      sourceDocumentId: detail.document.id,
      normalizedInstitutionId: course.student_institution_id,
      normalizedTermId: course.academic_term_id,
      institution: institutions.get(course.student_institution_id) || "Unknown institution",
      code: course.course_code,
      title: course.course_title,
      term: terms.get(course.academic_term_id) || "Unknown term",
      creditsAttempted: course.credits_attempted ?? 0,
      creditsEarned: course.credits_earned ?? 0,
      grade: course.grade ?? "",
      status: course.course_status === "in_progress" ? "in-progress" : "completed",
      confidence: course.extraction_confidence >= 0.9 ? "high" : course.extraction_confidence >= 0.75 ? "medium" : "low",
      repeat: course.repeat_indicator,
      transfer: course.transfer_indicator,
      extractionConfidence: course.extraction_confidence,
      sourcePage: course.source_page,
      rawText: course.source_raw_text ?? undefined,
    })),
    examCredits: detail.examCredits.map((exam) => ({
      id: exam.id,
      normalizedRecordId: exam.id,
      sourceDocumentId: detail.document.id,
      type: exam.exam_type === "other" ? "Other" : exam.exam_type as ExamCredit["type"],
      subject: exam.subject,
      score: exam.score ?? "",
      creditsAwarded: exam.credits_awarded ?? 0,
      enabled: true,
      extractionConfidence: exam.extraction_confidence,
      sourcePage: exam.source_page,
    })),
    cumulativeGpa: detail.summary?.cumulative_gpa ?? 0,
    extractionStatus: "complete",
    verificationStatus: "reviewing",
  };
}

function mergeTranscripts(items: TranscriptData[]): TranscriptData {
  const institutions = [...new Set(items.flatMap((item) => item.institutions))];
  return {
    id: items[0]?.id ?? crypto.randomUUID(),
    fileName: items.length === 1 ? items[0].fileName : `${items.length} transcript PDFs`,
    institutions,
    courses: items.flatMap((item) => item.courses.map((course) => ({
      ...course,
      id: course.normalizedRecordId ? course.id : `${item.id}:${course.id}`,
      sourceDocumentId: course.sourceDocumentId ?? item.id,
    }))),
    examCredits: items.flatMap((item) => item.examCredits.map((exam) => ({
      ...exam,
      id: exam.normalizedRecordId ? exam.id : `${item.id}:${exam.id}`,
      sourceDocumentId: exam.sourceDocumentId ?? item.id,
    }))),
    cumulativeGpa: items[0]?.cumulativeGpa ?? 0,
    extractionStatus: "complete",
    verificationStatus: "reviewing",
  };
}

export default function TranscriptPage() {
  const router = useRouter();
  const fileInput = useRef<HTMLInputElement>(null);
  const { transcript, setTranscript } = useApp();
  const [choice, setChoice] = useState<InputChoice>(null);
  const [loading, setLoading] = useState(false);
  const [stage, setStage] = useState<ProgressStage>("uploading");
  const [error, setError] = useState("");
  const [documents, setDocuments] = useState<UploadedDocumentView[]>([]);
  const [warnings, setWarnings] = useState<ReviewWarning[]>([]);
  const [lastFiles, setLastFiles] = useState<File[]>([]);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [sourceCourse, setSourceCourse] = useState<CourseRecord | null>(null);
  const [examOpen, setExamOpen] = useState(true);

  const processOneFile = async (file: File | null, token: string | null) => {
    const form = new FormData();
    if (file) form.set("transcript", file);
    if (token && file) {
      setStage("uploading");
      const upload = await fetch("/api/transcript-documents", { method: "POST", headers: { Authorization: `Bearer ${token}` }, body: form });
      const uploaded = await upload.json() as { data?: { id: string; original_filename: string }; error?: string; detail?: string };
      if (!upload.ok || !uploaded.data) throw new Error(uploaded.detail || uploaded.error || "Private upload failed.");
      setStage("parsing");
      const parsed = await fetch(`/api/transcript-documents/${uploaded.data.id}/parse`, { method: "POST", headers: { Authorization: `Bearer ${token}` } });
      setStage("validating");
      const payload = await parsed.json() as { data?: { pipeline: TranscriptPipelineResult; detail: DetailedTranscript }; error?: string; detail?: string };
      if (!parsed.ok || !payload.data?.detail) throw new Error(payload.detail || payload.error || "Transcript parsing failed.");
      return {
        transcript: detailToPlannerData(payload.data.detail),
        document: { id: uploaded.data.id, fileName: uploaded.data.original_filename, status: payload.data.pipeline.status as "needs_review" | "completed", mode: "supabase" as const },
        warnings: payload.data.detail.warnings.map((item) => ({
          id: item.id, sourceDocumentId: uploaded.data!.id, code: item.warning_code, severity: item.severity,
          state: item.state, message: item.message, entityId: item.entity_source_id, pageNumber: item.source_page,
        })),
      };
    }

    setStage(file ? "extracting" : "parsing");
    const response = await fetch("/api/transcript/extract", { method: "POST", body: form });
    setStage("validating");
    const payload = await response.json() as { data?: TranscriptData; pipeline?: TranscriptPipelineResult; error?: string; detail?: string };
    if (!response.ok || !payload.data || !payload.pipeline) throw new Error(payload.detail || payload.error || "Transcript extraction failed.");
    return {
      transcript: payload.data,
      document: { id: payload.pipeline.documentId, fileName: payload.pipeline.fileName, status: payload.pipeline.status as "needs_review" | "completed", mode: "sample" as const },
      warnings: payload.pipeline.validatedTranscript.warnings.map((item) => ({
        id: item.id, code: item.code, severity: item.severity, state: item.state, message: item.message,
        entityId: item.entityId, pageNumber: item.source?.pageNumber ?? null,
      })),
    };
  };

  const loadPdfs = async (files: File[] = []) => {
    const invalid = files.find((file) => file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf"));
    if (invalid) {
      setError(`${invalid.name} is not a PDF file.`);
      return;
    }
    const tooLarge = files.find((file) => file.size > 15 * 1024 * 1024);
    if (tooLarge) {
      setError(`${tooLarge.name} is larger than 15 MB.`);
      return;
    }
    setChoice("pdf");
    setLoading(true);
    setError("");
    setLastFiles(files);
    setDocuments([]);
    setWarnings([]);
    try {
      const supabase = getSupabaseBrowserClient();
      const session = supabase ? await supabase.auth.getSession() : null;
      const token = session?.data.session?.access_token ?? null;
      setAccessToken(token);
      const inputs: Array<File | null> = files.length ? files : [null];
      const results = [];
      for (const file of inputs) results.push(await processOneFile(file, token));
      setStage("review");
      setTranscript(mergeTranscripts(results.map((item) => item.transcript)));
      setDocuments(results.map((item) => item.document));
      setWarnings(results.flatMap((item) => item.warnings));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "We could not read that PDF. Try manual entry instead.");
      setChoice(null);
    } finally {
      setLoading(false);
    }
  };

  const startManual = () => {
    setChoice("manual");
    setWarnings([]);
    setDocuments([]);
    setTranscript({
      id: crypto.randomUUID(), institutions: [transcript.institutions[0] || ""], courses: [], examCredits: [], cumulativeGpa: 0,
      extractionStatus: "complete", verificationStatus: "reviewing",
    });
  };

  const updateCourse = (id: string, patch: Partial<CourseRecord>) => {
    setTranscript({ ...transcript, verificationStatus: "reviewing", courses: transcript.courses.map((course) => course.id === id ? { ...course, ...patch } : course) });
  };

  const addCourse = () => {
    const anchor = transcript.courses[0];
    const course: CourseRecord = {
      id: `manual-${Date.now()}`, institution: anchor?.institution || transcript.institutions[0] || "", code: "", title: "", term: anchor?.term || "Fall 2026",
      creditsAttempted: 5, creditsEarned: 0, grade: "IP", status: "planned", confidence: "high", repeat: false, transfer: false,
      sourceDocumentId: anchor?.sourceDocumentId, normalizedInstitutionId: anchor?.normalizedInstitutionId, normalizedTermId: anchor?.normalizedTermId,
    };
    setTranscript({ ...transcript, courses: [...transcript.courses, course] });
  };

  const removeCourse = async (course: CourseRecord) => {
    setTranscript({ ...transcript, courses: transcript.courses.filter((item) => item.id !== course.id) });
    if (accessToken && course.sourceDocumentId && course.normalizedRecordId) {
      await fetch(`/api/transcript-documents/${course.sourceDocumentId}/courses/${course.normalizedRecordId}`, { method: "DELETE", headers: { Authorization: `Bearer ${accessToken}` } });
    }
  };

  const updateExam = (id: string, patch: Partial<ExamCredit>) => {
    setTranscript({ ...transcript, examCredits: transcript.examCredits.map((exam) => exam.id === id ? { ...exam, ...patch } : exam) });
  };

  const addExam = () => {
    setTranscript({ ...transcript, examCredits: [...transcript.examCredits, { id: `manual-exam-${Date.now()}`, type: "AP", subject: "", score: "", creditsAwarded: 0, enabled: true, sourceDocumentId: documents[0]?.id }] });
    setExamOpen(true);
  };

  const resolveWarning = async (item: ReviewWarning) => {
    setWarnings((current) => current.map((warning) => warning.id === item.id ? { ...warning, state: "resolved" } : warning));
    if (accessToken && item.sourceDocumentId) {
      await fetch(`/api/transcript-documents/${item.sourceDocumentId}/warnings/${item.id}`, {
        method: "PATCH", headers: { Authorization: `Bearer ${accessToken}`, "Content-Type": "application/json" }, body: JSON.stringify({ state: "resolved", note: "Checked by the user during transcript review." }),
      });
    }
  };

  const saveReviewedCourses = async () => {
    if (!accessToken) return;
    for (const course of transcript.courses) {
      if (!course.sourceDocumentId || !course.normalizedInstitutionId || !course.normalizedTermId) continue;
      const body = {
        student_institution_id: course.normalizedInstitutionId, academic_term_id: course.normalizedTermId,
        course_code: course.code, course_title: course.title, credits_attempted: course.creditsAttempted, credits_earned: course.creditsEarned,
        grade: course.grade, course_status: course.status === "in-progress" ? "in_progress" : course.status === "planned" ? "unknown" : "completed",
        repeat_indicator: course.repeat, transfer_indicator: course.transfer, source_page: course.sourcePage ?? 1,
      };
      const path = course.normalizedRecordId
        ? `/api/transcript-documents/${course.sourceDocumentId}/courses/${course.normalizedRecordId}`
        : `/api/transcript-documents/${course.sourceDocumentId}/courses`;
      await fetch(path, { method: course.normalizedRecordId ? "PATCH" : "POST", headers: { Authorization: `Bearer ${accessToken}`, "Content-Type": "application/json" }, body: JSON.stringify(body) });
    }
  };

  const continueFlow = async () => {
    if (warnings.some((item) => item.state === "open" && item.severity === "blocking")) {
      setError("Resolve the blocking transcript checks before continuing.");
      return;
    }
    try {
      await saveReviewedCourses();
      if (accessToken) {
        for (const document of documents.filter((item) => item.mode === "supabase")) {
          const response = await fetch(`/api/transcript-documents/${document.id}/confirm`, { method: "POST", headers: { Authorization: `Bearer ${accessToken}` } });
          if (!response.ok) throw new Error("One transcript still has an unresolved blocking check.");
        }
      }
      setTranscript({ ...transcript, verificationStatus: "confirmed" });
      router.push("/targets");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not confirm the transcript.");
    }
  };

  if (!choice) {
    return (
      <main className="mx-auto flex min-h-[calc(100vh-130px)] max-w-3xl items-center px-5 py-12">
        <section className="w-full text-center">
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-teal-700">Your transcript</p>
          <h1 className="mt-3 text-3xl font-semibold tracking-[-0.045em] text-[var(--ink)] sm:text-4xl">Add your academic record.</h1>
          <p className="mx-auto mt-3 max-w-xl text-slate-500">Upload one or more PDFs. You will review every extracted course before it affects your plan.</p>
          <input ref={fileInput} type="file" multiple accept="application/pdf,.pdf" className="hidden" onChange={(event) => void loadPdfs(Array.from(event.target.files ?? []))} />
          <div className="card mx-auto mt-8 max-w-xl p-5 sm:p-7">
            <button onClick={() => fileInput.current?.click()} className="group flex w-full flex-col items-center rounded-2xl border-2 border-dashed border-teal-200 bg-teal-50/40 px-6 py-12 transition hover:border-teal-400 hover:bg-teal-50">
              <span className="grid size-14 place-items-center rounded-2xl bg-white text-teal-700 shadow-sm transition group-hover:-translate-y-0.5"><UploadCloud className="size-6" /></span>
              <span className="mt-4 text-base font-semibold text-slate-900">Upload PDF transcript</span>
              <span className="mt-1 text-sm text-slate-500">PDF only · up to 15 MB each · multiple schools supported</span>
            </button>
            <button onClick={() => void loadPdfs()} className="mt-3 text-xs font-semibold text-teal-700 hover:underline">Or try a sample transcript</button>
            <div className="my-6 flex items-center gap-3"><span className="h-px flex-1 bg-slate-200" /><span className="text-xs font-medium text-slate-400">or</span><span className="h-px flex-1 bg-slate-200" /></div>
            <button onClick={startManual} className="secondary-button w-full"><Pencil className="size-4" /> Enter courses manually</button>
            {error && <p className="mt-4 text-sm text-rose-600">{error}</p>}
          </div>
          <p className="mx-auto mt-4 flex max-w-xl items-center justify-center gap-2 text-xs text-slate-400"><ShieldCheck className="size-3.5" /> Signed-in uploads use private storage and are never treated as verified academic policy.</p>
        </section>
      </main>
    );
  }

  if (loading) {
    const stages = Object.keys(progressCopy) as ProgressStage[];
    const currentIndex = stages.indexOf(stage);
    return (
      <main className="mx-auto flex min-h-[calc(100vh-130px)] max-w-xl items-center justify-center px-5">
        <section className="card w-full p-7 text-center">
          <LoaderCircle className="mx-auto size-9 animate-spin text-teal-600" />
          <h1 className="mt-4 text-xl font-semibold text-slate-900">{progressCopy[stage]}…</h1>
          <p className="mt-2 text-sm text-slate-500">The extracted record stays provisional until you confirm it.</p>
          <div className="mt-6 grid grid-cols-5 gap-2">{stages.map((item, index) => <span key={item} className={`h-1.5 rounded-full ${index <= currentIndex ? "bg-teal-500" : "bg-slate-100"}`} />)}</div>
        </section>
      </main>
    );
  }

  const earned = transcript.courses.filter((course) => course.status === "completed").reduce((sum, course) => sum + course.creditsEarned, 0);
  const openWarnings = warnings.filter((item) => item.state === "open");

  return (
    <main className="mx-auto max-w-6xl px-5 py-10 lg:px-8 lg:py-12">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-teal-700"><Check className="size-3.5" /> {choice === "pdf" ? "Ready for your review" : "Manual entry"}</div>
          <h1 className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-[var(--ink)]">Check what we found.</h1>
          <p className="mt-2 text-sm text-slate-500">Edit any value directly. Page links show where an extracted row came from.</p>
        </div>
        <div className="flex flex-wrap gap-2"><button onClick={() => { setChoice(null); setError(""); }} className="secondary-button">Start over</button>{choice === "pdf" && <button onClick={() => void loadPdfs(lastFiles)} className="secondary-button"><RefreshCw className="size-4" /> Retry</button>}<button onClick={addCourse} className="secondary-button"><Plus className="size-4" /> Add course</button></div>
      </div>

      {documents.length > 0 && <div className="mt-6 flex flex-wrap gap-2">{documents.map((document) => <div key={document.id} className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs"><FileText className="size-4 text-teal-600" /><span className="font-semibold text-slate-700">{document.fileName}</span><span className={`rounded-full px-2 py-0.5 ${document.mode === "sample" ? "bg-amber-50 text-amber-700" : "bg-teal-50 text-teal-700"}`}>{document.mode === "sample" ? "Sample data" : "Private upload"}</span></div>)}</div>}

      {documents.some((item) => item.mode === "sample") && <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900"><strong>Demo extraction:</strong> these filled rows are sample data and were not read from your uploaded PDF. Configure Supabase, Docling, and OpenAI to enable live extraction.</div>}

      {openWarnings.length > 0 && (
        <section className="mt-4 rounded-2xl border border-amber-200 bg-amber-50/70 p-4">
          <div className="flex items-center gap-2"><AlertTriangle className="size-4 text-amber-700" /><h2 className="text-sm font-semibold text-amber-950">{openWarnings.length} item{openWarnings.length === 1 ? "" : "s"} to check</h2></div>
          <div className="mt-3 grid gap-2 md:grid-cols-2">{openWarnings.map((item) => <div key={item.id} className="rounded-xl bg-white p-3 text-sm shadow-sm"><div className="flex items-start justify-between gap-3"><div><p className="font-medium text-slate-800">{item.message}</p><p className="mt-1 text-xs text-slate-400">{item.pageNumber ? `Source: PDF page ${item.pageNumber}` : "Document-level check"} · {item.severity}</p></div><button onClick={() => void resolveWarning(item)} className="shrink-0 rounded-lg bg-teal-50 px-2.5 py-1.5 text-xs font-semibold text-teal-700">Mark checked</button></div></div>)}</div>
        </section>
      )}

      <section className="card mt-4 overflow-hidden">
        {transcript.courses.length === 0 ? (
          <div className="flex min-h-72 flex-col items-center justify-center px-5 text-center"><div className="grid size-12 place-items-center rounded-2xl bg-slate-100 text-slate-400"><Pencil className="size-5" /></div><h2 className="mt-4 font-semibold text-slate-900">Add your first course</h2><p className="mt-1 text-sm text-slate-500">Course code, title, credits, and grade are enough to start.</p><button onClick={addCourse} className="primary-button mt-5"><Plus className="size-4" /> Add course</button></div>
        ) : (
          <div className="overflow-x-auto"><table className="w-full min-w-[1060px] text-left">
            <thead className="border-b border-slate-200 bg-slate-50 text-[11px] font-semibold uppercase tracking-wide text-slate-400"><tr><th className="px-4 py-3">Institution</th><th className="px-3 py-3">Course</th><th className="px-3 py-3">Title</th><th className="px-3 py-3">Term</th><th className="px-3 py-3">Attempted</th><th className="px-3 py-3">Earned</th><th className="px-3 py-3">Grade</th><th className="px-3 py-3">Status</th><th className="px-3 py-3">Source</th><th className="w-12" /></tr></thead>
            <tbody className="divide-y divide-slate-100">{transcript.courses.map((course) => <tr key={course.id} className={course.extractionConfidence !== undefined && course.extractionConfidence < 0.75 ? "bg-amber-50/45" : "hover:bg-teal-50/30"}>
              <td className="px-4 py-2.5"><input aria-label={`Institution ${course.id}`} value={course.institution} onChange={(event) => updateCourse(course.id, { institution: event.target.value })} className="w-36 rounded-lg border border-transparent bg-transparent px-2 py-2 text-xs outline-none focus:border-teal-300 focus:bg-white" /></td>
              <td className="px-3 py-2.5"><input aria-label={`Course code ${course.id}`} value={course.code} onChange={(event) => updateCourse(course.id, { code: event.target.value })} className="w-24 rounded-lg border border-transparent bg-transparent px-2 py-2 text-sm font-semibold outline-none focus:border-teal-300 focus:bg-white" /></td>
              <td className="px-3 py-2.5"><input aria-label={`Course title ${course.id}`} value={course.title} onChange={(event) => updateCourse(course.id, { title: event.target.value })} className="w-48 rounded-lg border border-transparent bg-transparent px-2 py-2 text-sm outline-none focus:border-teal-300 focus:bg-white" /></td>
              <td className="px-3 py-2.5"><input aria-label={`Course term ${course.id}`} value={course.term} onChange={(event) => updateCourse(course.id, { term: event.target.value })} className="w-28 rounded-lg border border-transparent bg-transparent px-2 py-2 text-sm text-slate-600 outline-none focus:border-teal-300 focus:bg-white" /></td>
              <td className="px-3 py-2.5"><input aria-label={`Attempted credits ${course.id}`} type="number" min="0" step="0.5" value={course.creditsAttempted} onChange={(event) => updateCourse(course.id, { creditsAttempted: Number(event.target.value) })} className="w-16 rounded-lg border border-slate-200 px-2 py-2 text-sm outline-none focus:border-teal-400" /></td>
              <td className="px-3 py-2.5"><input aria-label={`Earned credits ${course.id}`} type="number" min="0" step="0.5" value={course.creditsEarned} onChange={(event) => updateCourse(course.id, { creditsEarned: Number(event.target.value) })} className="w-16 rounded-lg border border-slate-200 px-2 py-2 text-sm outline-none focus:border-teal-400" /></td>
              <td className="px-3 py-2.5"><input aria-label={`Grade ${course.id}`} value={course.grade} onChange={(event) => updateCourse(course.id, { grade: event.target.value })} className="w-14 rounded-lg border border-slate-200 px-2 py-2 text-sm outline-none focus:border-teal-400" /></td>
              <td className="px-3 py-2.5"><select aria-label={`Status ${course.id}`} value={course.status} onChange={(event) => updateCourse(course.id, { status: event.target.value as CourseRecord["status"] })} className="rounded-lg border border-slate-200 bg-white px-2 py-2 text-xs"><option value="completed">Completed</option><option value="in-progress">In progress</option><option value="planned">Planned</option></select></td>
              <td className="px-3 py-2.5">{course.sourcePage ? <button onClick={() => setSourceCourse(course)} className="rounded-lg border border-slate-200 px-2 py-1.5 text-xs font-semibold text-slate-600 hover:border-teal-300 hover:text-teal-700">Page {course.sourcePage}<span className={`ml-1 ${course.extractionConfidence !== undefined && course.extractionConfidence < 0.75 ? "text-amber-700" : "text-slate-400"}`}>· {confidenceLabel(course.extractionConfidence)}</span></button> : <span className="text-xs text-slate-300">Manual</span>}</td>
              <td className="pr-3"><button aria-label={`Delete ${course.code || "course"}`} onClick={() => void removeCourse(course)} className="rounded-lg p-2 text-slate-300 hover:bg-rose-50 hover:text-rose-500"><Trash2 className="size-4" /></button></td>
            </tr>)}</tbody>
          </table></div>
        )}
      </section>

      <section className="card mt-4 overflow-hidden">
        <button onClick={() => setExamOpen((value) => !value)} className="flex w-full items-center justify-between px-5 py-4 text-left"><div><h2 className="text-sm font-semibold text-slate-900">AP, IB, CLEP, and other exam credit</h2><p className="mt-0.5 text-xs text-slate-500">Transcript extraction only records what is printed; later policy analysis decides applicability.</p></div>{examOpen ? <ChevronUp className="size-4 text-slate-400" /> : <ChevronDown className="size-4 text-slate-400" />}</button>
        {examOpen && <div className="border-t border-slate-100 px-5 py-4"><div className="grid gap-2">{transcript.examCredits.map((exam) => <div key={exam.id} className="grid gap-2 rounded-xl bg-slate-50 p-3 sm:grid-cols-[90px_1fr_90px_100px_40px]"><select value={exam.type} onChange={(event) => updateExam(exam.id, { type: event.target.value as ExamCredit["type"] })} className="rounded-lg border border-slate-200 bg-white px-2 py-2 text-sm"><option>AP</option><option>IB</option><option>CLEP</option><option>Other</option></select><input aria-label="Exam subject" value={exam.subject} onChange={(event) => updateExam(exam.id, { subject: event.target.value })} placeholder="Subject" className="rounded-lg border border-slate-200 px-3 py-2 text-sm" /><input aria-label="Exam score" value={exam.score} onChange={(event) => updateExam(exam.id, { score: event.target.value })} placeholder="Score" className="rounded-lg border border-slate-200 px-3 py-2 text-sm" /><input aria-label="Credits awarded" type="number" min="0" step="0.5" value={exam.creditsAwarded} onChange={(event) => updateExam(exam.id, { creditsAwarded: Number(event.target.value) })} className="rounded-lg border border-slate-200 px-3 py-2 text-sm" /><button aria-label="Remove exam" onClick={() => setTranscript({ ...transcript, examCredits: transcript.examCredits.filter((item) => item.id !== exam.id) })} className="grid place-items-center text-slate-300 hover:text-rose-500"><X className="size-4" /></button></div>)}</div><button onClick={addExam} className="mt-3 inline-flex items-center gap-1.5 text-xs font-semibold text-teal-700"><Plus className="size-3.5" /> Add exam credit</button></div>}
      </section>

      {sourceCourse && <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/35 p-5" onClick={() => setSourceCourse(null)}><div className="w-full max-w-lg rounded-2xl bg-white p-5 shadow-2xl" onClick={(event) => event.stopPropagation()}><div className="flex items-start justify-between gap-4"><div><div className="flex items-center gap-2 text-xs font-semibold text-teal-700"><FileSearch className="size-4" /> PDF page {sourceCourse.sourcePage}</div><h2 className="mt-2 text-lg font-semibold text-slate-900">{sourceCourse.code} · {sourceCourse.title}</h2></div><button aria-label="Close source evidence" onClick={() => setSourceCourse(null)} className="rounded-lg p-2 text-slate-400 hover:bg-slate-100"><X className="size-4" /></button></div><div className="mt-4 rounded-xl bg-slate-50 p-4"><p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Parser evidence</p><p className="mt-2 text-sm leading-6 text-slate-700">{sourceCourse.rawText || "No text excerpt is available for this row. Open the original private PDF to verify the page."}</p></div><p className="mt-3 text-xs text-slate-500">Extraction confidence: {confidenceLabel(sourceCourse.extractionConfidence)}{sourceCourse.extractionConfidence !== undefined ? ` (${Math.round(sourceCourse.extractionConfidence * 100)}%)` : ""}. Confidence measures transcription certainty only.</p></div></div>}

      {error && <p className="mt-4 rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</p>}
      <div className="mt-5 flex flex-col gap-3 rounded-2xl bg-[var(--ink)] p-4 text-white sm:flex-row sm:items-center sm:justify-between">
        <div><p className="text-sm font-semibold">{transcript.courses.length} courses · {earned} earned credits</p><p className="mt-0.5 text-xs text-slate-300">{openWarnings.length ? `${openWarnings.length} review item${openWarnings.length === 1 ? "" : "s"} still open.` : "All extraction checks are reviewed."}</p></div>
        <button disabled={transcript.courses.length === 0} onClick={() => void continueFlow()} className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-[var(--lime)] px-4 text-sm font-semibold text-[var(--ink)] disabled:opacity-50">Confirm transcript and choose schools <ArrowRight className="size-4" /></button>
      </div>
    </main>
  );
}
