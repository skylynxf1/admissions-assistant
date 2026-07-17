export type TranscriptDocumentStatus = "uploaded" | "processing" | "needs_review" | "completed" | "failed";
export type TranscriptParserName = "docling" | "marker" | "pymupdf" | "sample";
export type TranscriptCourseStatus = "completed" | "in_progress" | "withdrawn" | "failed" | "audit" | "unknown";
export type TranscriptWarningSeverity = "info" | "warning" | "blocking";
export type TranscriptWarningState = "open" | "resolved" | "dismissed";

export interface TranscriptSourceReference {
  pageNumber: number;
  parserBlockIds: string[];
  rawText: string | null;
}

export interface ParsedTranscriptBlock {
  id: string;
  pageNumber: number;
  type: "text" | "table" | "heading" | "other";
  text: string;
  boundingBox: [number, number, number, number] | null;
}

export interface ParsedTranscriptPage {
  pageNumber: number;
  markdown: string;
  text: string;
  blocks: ParsedTranscriptBlock[];
}

export interface ParsedTranscriptDocument {
  parser: TranscriptParserName;
  parserVersion: string;
  pageCount: number;
  markdown: string;
  pages: ParsedTranscriptPage[];
  metadata: Record<string, string | number | boolean | null>;
}

export interface ExtractedInstitution {
  id: string;
  name: string;
  studentIdentifier: string | null;
  attendanceStart: string | null;
  attendanceEnd: string | null;
  degreeName: string | null;
  degreeDate: string | null;
  confidence: number;
  source: TranscriptSourceReference;
}

export interface ExtractedAcademicTerm {
  id: string;
  institutionId: string;
  label: string;
  startDate: string | null;
  endDate: string | null;
  academicLevel: string | null;
  creditsAttempted: number | null;
  creditsEarned: number | null;
  termGpa: number | null;
  confidence: number;
  source: TranscriptSourceReference;
}

export interface ExtractedTranscriptCourse {
  id: string;
  institutionId: string;
  termId: string;
  courseCode: string;
  courseTitle: string;
  creditsAttempted: number | null;
  creditsEarned: number | null;
  grade: string | null;
  status: TranscriptCourseStatus;
  repeatIndicator: boolean;
  transferIndicator: boolean;
  confidence: number;
  source: TranscriptSourceReference;
}

export interface ExtractedExamCredit {
  id: string;
  examType: "AP" | "IB" | "CLEP" | "other";
  subject: string;
  score: string | null;
  creditsAwarded: number | null;
  confidence: number;
  source: TranscriptSourceReference;
}

export interface ExtractedTranscriptSummary {
  cumulativeGpa: number | null;
  totalCreditsAttempted: number | null;
  totalCreditsEarned: number | null;
  totalQualityPoints: number | null;
  degreeName: string | null;
  degreeDate: string | null;
  confidence: number;
  source: TranscriptSourceReference;
}

export interface TranscriptExtraction {
  documentType: "college_transcript" | "unknown";
  studentName: string | null;
  institutions: ExtractedInstitution[];
  terms: ExtractedAcademicTerm[];
  courses: ExtractedTranscriptCourse[];
  examCredits: ExtractedExamCredit[];
  summary: ExtractedTranscriptSummary;
}

export interface TranscriptValidationWarning {
  id: string;
  code: string;
  severity: TranscriptWarningSeverity;
  state: TranscriptWarningState;
  entityType: "document" | "institution" | "term" | "course" | "exam_credit" | "summary";
  entityId: string | null;
  message: string;
  details: Record<string, string | number | boolean | null>;
  source: TranscriptSourceReference | null;
}

export interface TranscriptValidationMetrics {
  courseCount: number;
  lowConfidenceCount: number;
  openWarningCount: number;
  blockingWarningCount: number;
  calculatedAttemptedCredits: number;
  calculatedEarnedCredits: number;
}

export interface ValidatedTranscript {
  extraction: TranscriptExtraction;
  warnings: TranscriptValidationWarning[];
  metrics: TranscriptValidationMetrics;
  requiresReview: boolean;
}

export interface TranscriptPipelineResult {
  documentId: string;
  fileName: string;
  status: TranscriptDocumentStatus;
  parseRunId: string;
  parsedDocument: ParsedTranscriptDocument;
  validatedTranscript: ValidatedTranscript;
  mode: "supabase" | "sample";
}
