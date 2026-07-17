import type {
  TranscriptExtraction,
  TranscriptSourceReference,
  TranscriptValidationWarning,
  ValidatedTranscript,
} from "@/lib/transcript/types";

const LOW_CONFIDENCE = 0.75;
const CREDIT_TOLERANCE = 0.5;

function warning(
  code: string,
  severity: TranscriptValidationWarning["severity"],
  entityType: TranscriptValidationWarning["entityType"],
  entityId: string | null,
  message: string,
  source: TranscriptSourceReference | null,
  details: TranscriptValidationWarning["details"] = {},
): TranscriptValidationWarning {
  return { id: `${code}-${entityId ?? "document"}`, code, severity, state: "open", entityType, entityId, message, source, details };
}

function isValidPage(source: TranscriptSourceReference, pageCount: number) {
  return Number.isInteger(source.pageNumber) && source.pageNumber >= 1 && source.pageNumber <= pageCount;
}

export function validateTranscriptExtraction(input: TranscriptExtraction, pageCount: number): ValidatedTranscript {
  const warnings: TranscriptValidationWarning[] = [];
  const institutionIds = new Set(input.institutions.map((item) => item.id));
  const termIds = new Set(input.terms.map((item) => item.id));
  const seenCourses = new Map<string, string>();

  const confidenceItems = [
    ...input.institutions.map((item) => ({ type: "institution" as const, item })),
    ...input.terms.map((item) => ({ type: "term" as const, item })),
    ...input.courses.map((item) => ({ type: "course" as const, item })),
    ...input.examCredits.map((item) => ({ type: "exam_credit" as const, item })),
  ];

  for (const { type, item } of confidenceItems) {
    if (item.confidence < 0 || item.confidence > 1) warnings.push(warning("invalid_confidence", "blocking", type, item.id, "Extraction confidence must be between 0 and 1.", item.source, { confidence: item.confidence }));
    else if (item.confidence < LOW_CONFIDENCE) warnings.push(warning("low_confidence", "warning", type, item.id, "This value was extracted with low confidence and should be checked against the PDF.", item.source, { confidence: item.confidence }));
    if (!isValidPage(item.source, pageCount)) warnings.push(warning("invalid_source_page", "blocking", type, item.id, "The cited source page is outside the PDF page range.", item.source, { pageCount }));
  }

  for (const term of input.terms) {
    if (!institutionIds.has(term.institutionId)) warnings.push(warning("unknown_institution", "blocking", "term", term.id, "This term does not reference a known institution.", term.source));
  }

  for (const course of input.courses) {
    if (!institutionIds.has(course.institutionId)) warnings.push(warning("unknown_institution", "blocking", "course", course.id, "This course does not reference a known institution.", course.source));
    if (!termIds.has(course.termId)) warnings.push(warning("unknown_term", "blocking", "course", course.id, "This course does not reference a known academic term.", course.source));
    if (!course.courseCode && !course.courseTitle) warnings.push(warning("missing_course_identity", "blocking", "course", course.id, "The course code and title are both missing.", course.source));
    for (const [field, value] of [["creditsAttempted", course.creditsAttempted], ["creditsEarned", course.creditsEarned]] as const) {
      if (value !== null && value < 0) warnings.push(warning("negative_credits", "blocking", "course", course.id, "Credits cannot be negative.", course.source, { field, value }));
    }
    if (course.creditsAttempted !== null && course.creditsEarned !== null && course.creditsEarned > course.creditsAttempted) {
      warnings.push(warning("earned_exceeds_attempted", "blocking", "course", course.id, "Earned credits exceed attempted credits.", course.source));
    }
    if (["failed", "withdrawn"].includes(course.status) && (course.creditsEarned ?? 0) > 0) {
      warnings.push(warning("status_credit_conflict", "warning", "course", course.id, "The course status conflicts with the earned-credit value.", course.source));
    }
    const key = `${course.institutionId}|${course.termId}|${course.courseCode.toUpperCase()}|${course.courseTitle.toUpperCase()}`;
    const prior = seenCourses.get(key);
    if (prior) warnings.push(warning("possible_duplicate", "warning", "course", course.id, "A possible duplicate course was found. Confirm whether it is a repeat.", course.source, { matchingCourseId: prior }));
    else seenCourses.set(key, course.id);
  }

  const calculatedAttemptedCredits = input.courses.reduce((sum, course) => sum + (course.creditsAttempted ?? 0), 0);
  const calculatedEarnedCredits = input.courses.reduce((sum, course) => sum + (course.creditsEarned ?? 0), 0);
  if (input.summary.totalCreditsAttempted !== null && Math.abs(input.summary.totalCreditsAttempted - calculatedAttemptedCredits) > CREDIT_TOLERANCE) {
    warnings.push(warning("attempted_total_mismatch", "warning", "summary", null, "The transcript attempted-credit total does not match the extracted course rows.", input.summary.source, { printedTotal: input.summary.totalCreditsAttempted, calculatedTotal: calculatedAttemptedCredits }));
  }
  if (input.summary.totalCreditsEarned !== null && Math.abs(input.summary.totalCreditsEarned - calculatedEarnedCredits) > CREDIT_TOLERANCE) {
    warnings.push(warning("earned_total_mismatch", "warning", "summary", null, "The transcript earned-credit total does not match the extracted course rows.", input.summary.source, { printedTotal: input.summary.totalCreditsEarned, calculatedTotal: calculatedEarnedCredits }));
  }
  if (input.summary.cumulativeGpa !== null && (input.summary.cumulativeGpa < 0 || input.summary.cumulativeGpa > 5)) {
    warnings.push(warning("gpa_out_of_range", "blocking", "summary", null, "The cumulative GPA is outside the supported 0–5 range.", input.summary.source, { value: input.summary.cumulativeGpa }));
  }

  const blockingWarningCount = warnings.filter((item) => item.severity === "blocking").length;
  const lowConfidenceCount = warnings.filter((item) => item.code === "low_confidence").length;
  return {
    extraction: input,
    warnings,
    metrics: {
      courseCount: input.courses.length,
      lowConfidenceCount,
      openWarningCount: warnings.length,
      blockingWarningCount,
      calculatedAttemptedCredits,
      calculatedEarnedCredits,
    },
    requiresReview: warnings.length > 0 || input.courses.length === 0,
  };
}
