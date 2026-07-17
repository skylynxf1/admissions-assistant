import { createSampleTranscript } from "@/data/sample-transcript";
import type { CourseRecord, TranscriptData } from "@/lib/types";
import type {
  ParsedTranscriptDocument,
  TranscriptExtraction,
  TranscriptPipelineResult,
  ValidatedTranscript,
} from "@/lib/transcript/types";
import { validateTranscriptExtraction } from "@/lib/transcript/validator";

function source(pageNumber: number, rawText: string) {
  return { pageNumber, parserBlockIds: [`sample-page-${pageNumber}`], rawText };
}

export function createSampleParsedDocument(): ParsedTranscriptDocument {
  return {
    parser: "sample",
    parserVersion: "1.0",
    pageCount: 2,
    markdown: "# SAMPLE TRANSCRIPT\n\nFictional demo transcript used when parsing services are not configured.",
    pages: [1, 2].map((pageNumber) => ({
      pageNumber,
      markdown: `## Sample page ${pageNumber}`,
      text: `Fictional sample transcript page ${pageNumber}`,
      blocks: [{ id: `sample-page-${pageNumber}`, pageNumber, type: "text", text: `Fictional sample transcript page ${pageNumber}`, boundingBox: null }],
    })),
    metadata: { sample: true },
  };
}

export function createSampleExtraction(): TranscriptExtraction {
  const transcript = createSampleTranscript();
  const institutions = transcript.institutions.map((name, index) => ({
    id: `institution-${index + 1}`,
    name,
    studentIdentifier: null,
    attendanceStart: null,
    attendanceEnd: null,
    degreeName: null,
    degreeDate: null,
    confidence: index === 0 ? 0.99 : 0.92,
    source: source(index + 1, name),
  }));
  const institutionIdByName = new Map(institutions.map((item) => [item.name, item.id]));
  const termLabels = [...new Set(transcript.courses.map((course) => course.term))];
  const terms = termLabels.map((label, index) => {
    const firstCourse = transcript.courses.find((course) => course.term === label)!;
    const courses = transcript.courses.filter((course) => course.term === label);
    return {
      id: `term-${index + 1}`,
      institutionId: institutionIdByName.get(firstCourse.institution)!,
      label,
      startDate: null,
      endDate: null,
      academicLevel: "Undergraduate",
      creditsAttempted: courses.reduce((sum, course) => sum + course.creditsAttempted, 0),
      creditsEarned: courses.reduce((sum, course) => sum + course.creditsEarned, 0),
      termGpa: null,
      confidence: 0.94,
      source: source(firstCourse.institution === transcript.institutions[0] ? 1 : 2, label),
    };
  });
  const termIdByLabel = new Map(terms.map((item) => [item.label, item.id]));
  const courses = transcript.courses.map((course) => ({
    id: course.id,
    institutionId: institutionIdByName.get(course.institution)!,
    termId: termIdByLabel.get(course.term)!,
    courseCode: course.code,
    courseTitle: course.title,
    creditsAttempted: course.creditsAttempted,
    creditsEarned: course.creditsEarned,
    grade: course.grade,
    status: course.status === "in-progress" ? "in_progress" as const : "completed" as const,
    repeatIndicator: course.repeat,
    transferIndicator: course.transfer,
    confidence: course.confidence === "high" ? 0.97 : 0.68,
    source: source(course.institution === transcript.institutions[0] ? 1 : 2, `${course.code} ${course.title}`),
  }));
  const attempted = courses.reduce((sum, course) => sum + (course.creditsAttempted ?? 0), 0);
  const earned = courses.reduce((sum, course) => sum + (course.creditsEarned ?? 0), 0);
  return {
    documentType: "college_transcript",
    studentName: "Sample Student",
    institutions,
    terms,
    courses,
    examCredits: transcript.examCredits.map((exam) => ({
      id: exam.id,
      examType: exam.type === "Other" ? "other" as const : exam.type,
      subject: exam.subject,
      score: exam.score,
      creditsAwarded: exam.creditsAwarded,
      confidence: 0.88,
      source: source(2, `${exam.type} ${exam.subject} ${exam.score}`),
    })),
    summary: {
      cumulativeGpa: transcript.cumulativeGpa,
      totalCreditsAttempted: attempted,
      totalCreditsEarned: earned,
      totalQualityPoints: null,
      degreeName: null,
      degreeDate: null,
      confidence: 0.93,
      source: source(2, `Cumulative GPA ${transcript.cumulativeGpa}`),
    },
  };
}

export function createSamplePipelineResult(fileName = "sample-transfer-transcript.pdf"): TranscriptPipelineResult {
  const parsedDocument = createSampleParsedDocument();
  const validatedTranscript = validateTranscriptExtraction(createSampleExtraction(), parsedDocument.pageCount);
  return {
    documentId: crypto.randomUUID(),
    fileName,
    status: "needs_review",
    parseRunId: crypto.randomUUID(),
    parsedDocument,
    validatedTranscript,
    mode: "sample",
  };
}

export function validatedTranscriptToPlannerData(validated: ValidatedTranscript, documentId: string, fileName: string): TranscriptData {
  const institutionNames = new Map(validated.extraction.institutions.map((item) => [item.id, item.name]));
  const termNames = new Map(validated.extraction.terms.map((item) => [item.id, item.label]));
  const courses: CourseRecord[] = validated.extraction.courses.map((course) => ({
    id: course.id,
    institution: institutionNames.get(course.institutionId) || "Unknown institution",
    code: course.courseCode,
    title: course.courseTitle,
    term: termNames.get(course.termId) || "Unknown term",
    creditsAttempted: course.creditsAttempted ?? 0,
    creditsEarned: course.creditsEarned ?? 0,
    grade: course.grade ?? "",
    status: course.status === "in_progress" ? "in-progress" : "completed",
    confidence: course.confidence >= 0.9 ? "high" : course.confidence >= 0.75 ? "medium" : "low",
    repeat: course.repeatIndicator,
    transfer: course.transferIndicator,
    sourcePage: course.source.pageNumber,
    extractionConfidence: course.confidence,
    rawText: course.source.rawText ?? undefined,
  }));
  return {
    id: documentId,
    fileName,
    institutions: validated.extraction.institutions.map((item) => item.name),
    courses,
    examCredits: validated.extraction.examCredits.map((exam) => ({
      id: exam.id,
      type: exam.examType === "other" ? "Other" : exam.examType,
      subject: exam.subject,
      score: exam.score ?? "",
      creditsAwarded: exam.creditsAwarded ?? 0,
      enabled: true,
      sourcePage: exam.source.pageNumber,
      extractionConfidence: exam.confidence,
    })),
    cumulativeGpa: validated.extraction.summary.cumulativeGpa ?? 0,
    extractionStatus: "complete",
    verificationStatus: "reviewing",
  };
}
