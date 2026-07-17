import type { TranscriptExtraction } from "@/lib/transcript/types";

// Deterministic only: preserve meaning and raw evidence; never infer missing academic facts.
export function normalizeTranscriptExtraction(input: TranscriptExtraction): TranscriptExtraction {
  return {
    ...input,
    studentName: input.studentName?.trim() || null,
    institutions: input.institutions.map((item) => ({ ...item, name: item.name.trim() })),
    terms: input.terms.map((item) => ({ ...item, label: item.label.trim() })),
    courses: input.courses.map((item) => ({
      ...item,
      courseCode: item.courseCode.trim().replace(/\s+/g, " ").toUpperCase(),
      courseTitle: item.courseTitle.trim().replace(/\s+/g, " "),
      grade: item.grade?.trim().toUpperCase() || null,
    })),
    examCredits: input.examCredits.map((item) => ({ ...item, subject: item.subject.trim() })),
  };
}
