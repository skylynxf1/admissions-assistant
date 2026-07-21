export interface SourceCourseInput {
  code: string;
  title?: string | null;
}

export interface TransferOutcome {
  source_course: SourceCourseInput;
  state: string;
  destination_outcomes: string[];
  credits_awarded: number | null;
  minimum_grade: string | null;
  conditions: Record<string, unknown>;
  evidence_refs: string[];
  detail: string | null;
}

export interface TransferOutcomeRequest {
  pathway_key: string;
  courses: SourceCourseInput[];
}

export interface TransferOutcomeResponse {
  pathway_key: string;
  source_institution_id: string;
  destination_institution_id: string;
  outcomes: TransferOutcome[];
}
