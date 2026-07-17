// Maintained from the checked-in migration. Once a project is linked, regenerate with:
// supabase gen types typescript --linked > lib/supabase/database.types.ts

export type Json = string | number | boolean | null | { [key: string]: Json | undefined } | Json[];

type Table<Row, Insert, Update> = {
  Row: Row;
  Insert: Insert;
  Update: Update;
  Relationships: [];
};

type Schema<Tables extends Record<string, unknown>, Enums extends Record<string, string> = Record<never, never>> = {
  Tables: Tables;
  Views: Record<never, never>;
  Functions: Record<never, never>;
  Enums: Enums;
  CompositeTypes: Record<never, never>;
};

export type ConfidenceLevel = "high" | "medium" | "low";
export type SourceType = "web_page" | "catalog" | "policy" | "articulation" | "pdf" | "json" | "csv" | "api";
export type ReviewStatus = "pending" | "approved" | "rejected" | "needs_review";

interface InstitutionRow {
  id: string;
  slug: string;
  name: string;
  short_name: string | null;
  institution_type: string;
  system_name: string | null;
  campus: string | null;
  city: string | null;
  state: string | null;
  country: string;
  timezone: string | null;
  metadata: Json;
  created_at: string;
  updated_at: string;
}

interface ProfileRow {
  id: string;
  display_name: string | null;
  current_institution_id: string | null;
  current_institution_name: string | null;
  institution_type: string | null;
  residency_status: string | null;
  citizenship_status: string | null;
  home_state: string | null;
  intended_term: string | null;
  current_major: string | null;
  onboarding_state: Json;
  created_at: string;
  updated_at: string;
}

interface TranscriptRow {
  id: string;
  user_id: string;
  client_id: string | null;
  source_document_id: string | null;
  original_filename: string | null;
  extraction_status: "pending" | "extracting" | "complete" | "error";
  verification_status: "unreviewed" | "reviewing" | "confirmed";
  cumulative_gpa: number | null;
  extraction_metadata: Json;
  created_at: string;
  updated_at: string;
}

interface TranscriptDocumentRow {
  id: string; user_id: string; planner_transcript_id: string | null; original_filename: string;
  storage_bucket: string; storage_path: string; mime_type: string; size_bytes: number; content_hash_sha256: string;
  status: "uploaded" | "processing" | "needs_review" | "completed" | "failed"; active_parse_run_id: string | null;
  failure_code: string | null; failure_message: string | null; confirmed_at: string | null; created_at: string; updated_at: string;
}

interface TranscriptParseRunRow {
  id: string; document_id: string; sequence_number: number; parser_name: string; parser_version: string;
  extraction_model: string | null; extraction_schema_version: string; status: "queued" | "running" | "succeeded" | "failed";
  raw_parser_output: Json | null; raw_model_output: Json | null; validation_output: Json | null;
  error_code: string | null; error_message: string | null; started_at: string | null; completed_at: string | null; created_at: string;
}

interface TranscriptEvidenceRow {
  id: string; document_id: string; source_entity_id: string; extraction_confidence: number; source_page: number;
  source_block_ids: Json; source_raw_text: string | null; user_verified: boolean; created_at: string; updated_at: string;
}

interface ScenarioRow {
  id: string;
  user_id: string;
  client_id: string;
  name: string;
  planning_mode: string;
  priority_institution_id: string | null;
  transcript_id: string | null;
  profile_snapshot: Json;
  settings: Json;
  assumptions: Json;
  current_institution_id: string | null;
  target_term: string | null;
  max_credits: number | null;
  residency_status: string | null;
  institution_type: string | null;
  graduation_target: string | null;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}

export type Database = {
  public: Schema<Record<never, never>, { confidence_level: ConfidenceLevel }>;
  catalog: Schema<{
    institutions: Table<
      InstitutionRow,
      Partial<Pick<InstitutionRow, "id" | "short_name" | "system_name" | "campus" | "city" | "state" | "country" | "timezone" | "metadata">> & Pick<InstitutionRow, "slug" | "name" | "institution_type">,
      Partial<Omit<InstitutionRow, "id" | "created_at">>
    >;
    programs: Table<
      { id: string; institution_id: string; slug: string; name: string; campus: string | null; degree_type: string | null; program_type: string; metadata: Json },
      { id?: string; institution_id: string; slug: string; name: string; campus?: string | null; degree_type?: string | null; program_type: string; metadata?: Json },
      { slug?: string; name?: string; campus?: string | null; degree_type?: string | null; program_type?: string; metadata?: Json }
    >;
  }>;
  source: Schema<{
    pages: Table<
      { id: string; institution_id: string; original_url: string; canonical_url: string; page_title: string | null; source_type: SourceType; official: boolean; active: boolean; first_seen_at: string; last_seen_at: string; metadata: Json },
      { id?: string; institution_id: string; original_url: string; canonical_url: string; page_title?: string | null; source_type: SourceType; official?: boolean; active?: boolean; first_seen_at?: string; last_seen_at?: string; metadata?: Json },
      { original_url?: string; page_title?: string | null; source_type?: SourceType; official?: boolean; active?: boolean; last_seen_at?: string; metadata?: Json }
    >;
    snapshots: Table<
      { id: string; page_id: string; crawl_job_id: string | null; retrieved_at: string; content_hash: string; mime_type: string | null; storage_bucket: string | null; storage_path: string | null; http_status: number | null; etag: string | null; catalog_year: string | null; effective_term: string | null; raw_text: string | null; response_metadata: Json; created_at: string },
      { id?: string; page_id: string; crawl_job_id?: string | null; retrieved_at: string; content_hash: string; mime_type?: string | null; storage_bucket?: string | null; storage_path?: string | null; http_status?: number | null; etag?: string | null; catalog_year?: string | null; effective_term?: string | null; raw_text?: string | null; response_metadata?: Json },
      { retrieved_at?: string; mime_type?: string | null; storage_bucket?: string | null; storage_path?: string | null; http_status?: number | null; etag?: string | null; catalog_year?: string | null; effective_term?: string | null; raw_text?: string | null; response_metadata?: Json }
    >;
    evidence_records: Table<
      { id: string; snapshot_id: string; parser_run_id: string | null; claim_key: string; claim_type: string; exact_quote: string; locator: Json; table_headers: Json | null; table_row: Json | null; footnotes: string[]; normalized_value: Json | null; effective_from: string | null; effective_to: string | null; confidence: ConfidenceLevel; review_status: ReviewStatus; reviewed_by: string | null; reviewed_at: string | null; created_at: string },
      { id?: string; snapshot_id: string; parser_run_id?: string | null; claim_key: string; claim_type: string; exact_quote: string; locator?: Json; table_headers?: Json | null; table_row?: Json | null; footnotes?: string[]; normalized_value?: Json | null; effective_from?: string | null; effective_to?: string | null; confidence: ConfidenceLevel; review_status?: ReviewStatus },
      { exact_quote?: string; locator?: Json; table_headers?: Json | null; table_row?: Json | null; footnotes?: string[]; normalized_value?: Json | null; effective_from?: string | null; effective_to?: string | null; confidence?: ConfidenceLevel; review_status?: ReviewStatus; reviewed_by?: string | null; reviewed_at?: string | null }
    >;
  }, { source_type: SourceType; review_status: ReviewStatus }>;
  student: Schema<{
    profiles: Table<
      ProfileRow,
      Pick<ProfileRow, "id"> & Partial<Omit<ProfileRow, "id" | "created_at" | "updated_at">>,
      Partial<Omit<ProfileRow, "id" | "created_at" | "updated_at">>
    >;
    transcripts: Table<
      TranscriptRow,
      Pick<TranscriptRow, "user_id"> & Partial<Omit<TranscriptRow, "id" | "user_id" | "created_at" | "updated_at">>,
      Partial<Omit<TranscriptRow, "id" | "user_id" | "created_at" | "updated_at">>
    >;
    transcript_documents: Table<
      TranscriptDocumentRow,
      Pick<TranscriptDocumentRow, "id" | "user_id" | "original_filename" | "storage_path" | "size_bytes" | "content_hash_sha256"> & Partial<Omit<TranscriptDocumentRow, "id" | "user_id" | "original_filename" | "storage_path" | "size_bytes" | "content_hash_sha256" | "created_at" | "updated_at">>,
      Partial<Omit<TranscriptDocumentRow, "id" | "user_id" | "created_at" | "updated_at">>
    >;
    transcript_parse_runs: Table<
      TranscriptParseRunRow,
      Pick<TranscriptParseRunRow, "document_id" | "sequence_number" | "parser_name" | "parser_version" | "status"> & Partial<Omit<TranscriptParseRunRow, "id" | "document_id" | "sequence_number" | "parser_name" | "parser_version" | "status" | "created_at">>,
      never
    >;
    transcript_pages: Table<
      { id: string; parse_run_id: string; page_number: number; markdown: string; plain_text: string; parser_blocks: Json; created_at: string },
      { id?: string; parse_run_id: string; page_number: number; markdown?: string; plain_text?: string; parser_blocks?: Json },
      never
    >;
    student_institutions: Table<
      TranscriptEvidenceRow & { institution_name: string; student_identifier: string | null; attendance_start: string | null; attendance_end: string | null; degree_name: string | null; degree_date: string | null },
      Pick<TranscriptEvidenceRow, "document_id" | "source_entity_id" | "extraction_confidence" | "source_page"> & { institution_name: string; student_identifier?: string | null; attendance_start?: string | null; attendance_end?: string | null; degree_name?: string | null; degree_date?: string | null; source_block_ids?: Json; source_raw_text?: string | null; user_verified?: boolean },
      Partial<Omit<TranscriptEvidenceRow, "id" | "document_id" | "created_at" | "updated_at"> & { institution_name: string; student_identifier: string | null; attendance_start: string | null; attendance_end: string | null; degree_name: string | null; degree_date: string | null }>
    >;
    academic_terms: Table<
      TranscriptEvidenceRow & { student_institution_id: string; label: string; start_date: string | null; end_date: string | null; academic_level: string | null; credits_attempted: number | null; credits_earned: number | null; term_gpa: number | null },
      Pick<TranscriptEvidenceRow, "document_id" | "source_entity_id" | "extraction_confidence" | "source_page"> & { student_institution_id: string; label: string; start_date?: string | null; end_date?: string | null; academic_level?: string | null; credits_attempted?: number | null; credits_earned?: number | null; term_gpa?: number | null; source_block_ids?: Json; source_raw_text?: string | null; user_verified?: boolean },
      Partial<Omit<TranscriptEvidenceRow, "id" | "document_id" | "created_at" | "updated_at"> & { student_institution_id: string; label: string; start_date: string | null; end_date: string | null; academic_level: string | null; credits_attempted: number | null; credits_earned: number | null; term_gpa: number | null }>
    >;
    transcript_courses: Table<
      TranscriptEvidenceRow & { student_institution_id: string; academic_term_id: string; course_code: string; course_title: string; credits_attempted: number | null; credits_earned: number | null; grade: string | null; course_status: string; repeat_indicator: boolean; transfer_indicator: boolean },
      Pick<TranscriptEvidenceRow, "document_id" | "source_entity_id" | "extraction_confidence" | "source_page"> & { student_institution_id: string; academic_term_id: string; course_code?: string; course_title?: string; credits_attempted?: number | null; credits_earned?: number | null; grade?: string | null; course_status: string; repeat_indicator?: boolean; transfer_indicator?: boolean; source_block_ids?: Json; source_raw_text?: string | null; user_verified?: boolean },
      Partial<Omit<TranscriptEvidenceRow, "id" | "document_id" | "created_at" | "updated_at"> & { student_institution_id: string; academic_term_id: string; course_code: string; course_title: string; credits_attempted: number | null; credits_earned: number | null; grade: string | null; course_status: string; repeat_indicator: boolean; transfer_indicator: boolean }>
    >;
    exam_credits: Table<
      TranscriptEvidenceRow & { exam_type: string; subject: string; score: string | null; credits_awarded: number | null },
      Pick<TranscriptEvidenceRow, "document_id" | "source_entity_id" | "extraction_confidence" | "source_page"> & { exam_type: string; subject: string; score?: string | null; credits_awarded?: number | null; source_block_ids?: Json; source_raw_text?: string | null; user_verified?: boolean },
      Partial<Omit<TranscriptEvidenceRow, "id" | "document_id" | "created_at" | "updated_at"> & { exam_type: string; subject: string; score: string | null; credits_awarded: number | null }>
    >;
    transcript_summaries: Table<
      { id: string; document_id: string; cumulative_gpa: number | null; total_credits_attempted: number | null; total_credits_earned: number | null; total_quality_points: number | null; degree_name: string | null; degree_date: string | null; extraction_confidence: number; source_page: number; source_block_ids: Json; source_raw_text: string | null; user_verified: boolean; created_at: string; updated_at: string },
      { id?: string; document_id: string; cumulative_gpa?: number | null; total_credits_attempted?: number | null; total_credits_earned?: number | null; total_quality_points?: number | null; degree_name?: string | null; degree_date?: string | null; extraction_confidence: number; source_page: number; source_block_ids?: Json; source_raw_text?: string | null; user_verified?: boolean },
      Partial<{ cumulative_gpa: number | null; total_credits_attempted: number | null; total_credits_earned: number | null; total_quality_points: number | null; degree_name: string | null; degree_date: string | null; extraction_confidence: number; source_page: number; source_block_ids: Json; source_raw_text: string | null; user_verified: boolean }>
    >;
    transcript_warnings: Table<
      { id: string; document_id: string; parse_run_id: string | null; client_warning_id: string; warning_code: string; severity: "info" | "warning" | "blocking"; state: "open" | "resolved" | "dismissed"; entity_type: string; entity_source_id: string | null; message: string; details: Json; source_page: number | null; source_block_ids: Json; resolution_note: string | null; resolved_at: string | null; created_at: string; updated_at: string },
      { id?: string; document_id: string; parse_run_id?: string | null; client_warning_id: string; warning_code: string; severity: "info" | "warning" | "blocking"; state?: "open" | "resolved" | "dismissed"; entity_type: string; entity_source_id?: string | null; message: string; details?: Json; source_page?: number | null; source_block_ids?: Json; resolution_note?: string | null; resolved_at?: string | null },
      Partial<{ state: "open" | "resolved" | "dismissed"; resolution_note: string | null; resolved_at: string | null; message: string; details: Json }>
    >;
    transcript_review_actions: Table<
      { id: string; document_id: string; user_id: string; action_type: string; entity_type: string; entity_id: string | null; field_name: string | null; previous_value: Json | null; new_value: Json | null; note: string | null; created_at: string },
      { id?: string; document_id: string; user_id: string; action_type: string; entity_type: string; entity_id?: string | null; field_name?: string | null; previous_value?: Json | null; new_value?: Json | null; note?: string | null },
      never
    >;
    transcript_institutions: Table<
      { id: string; transcript_id: string; institution_id: string | null; institution_name: string; attended_from: string | null; attended_to: string | null; is_primary: boolean; created_at: string },
      { id?: string; transcript_id: string; institution_id?: string | null; institution_name: string; attended_from?: string | null; attended_to?: string | null; is_primary?: boolean },
      { institution_id?: string | null; institution_name?: string; attended_from?: string | null; attended_to?: string | null; is_primary?: boolean }
    >;
    course_records: Table<
      { id: string; transcript_id: string; transcript_institution_id: string | null; institution_id: string | null; client_id: string | null; institution_name: string; subject: string | null; number: string | null; course_code: string; course_title: string; term: string; credits_attempted: number; credits_earned: number; grade: string | null; course_status: string; repeat_indicator: boolean; transfer_indicator: boolean; in_progress: boolean; extraction_confidence: ConfidenceLevel; user_verified: boolean; extraction_evidence: Json; notes: string | null; created_at: string; updated_at: string },
      { id?: string; transcript_id: string; transcript_institution_id?: string | null; institution_id?: string | null; client_id?: string | null; institution_name: string; subject?: string | null; number?: string | null; course_code: string; course_title: string; term: string; credits_attempted?: number; credits_earned?: number; grade?: string | null; course_status: string; repeat_indicator?: boolean; transfer_indicator?: boolean; in_progress?: boolean; extraction_confidence: ConfidenceLevel; user_verified?: boolean; extraction_evidence?: Json; notes?: string | null },
      { institution_name?: string; subject?: string | null; number?: string | null; course_code?: string; course_title?: string; term?: string; credits_attempted?: number; credits_earned?: number; grade?: string | null; course_status?: string; repeat_indicator?: boolean; transfer_indicator?: boolean; in_progress?: boolean; extraction_confidence?: ConfidenceLevel; user_verified?: boolean; extraction_evidence?: Json; notes?: string | null }
    >;
    exam_scores: Table<
      { id: string; user_id: string; transcript_id: string | null; client_id: string | null; exam_type: string; subject: string; score: string; exam_date: string | null; reported_institution_id: string | null; credits_awarded: number | null; enabled: boolean; user_verified: boolean; created_at: string },
      { id?: string; user_id: string; transcript_id?: string | null; client_id?: string | null; exam_type: string; subject: string; score: string; exam_date?: string | null; reported_institution_id?: string | null; credits_awarded?: number | null; enabled?: boolean; user_verified?: boolean },
      { transcript_id?: string | null; exam_type?: string; subject?: string; score?: string; exam_date?: string | null; reported_institution_id?: string | null; credits_awarded?: number | null; enabled?: boolean; user_verified?: boolean }
    >;
  }>;
  planning: Schema<{
    scenarios: Table<
      ScenarioRow,
      Pick<ScenarioRow, "user_id" | "client_id" | "name" | "planning_mode" | "profile_snapshot" | "settings"> & Partial<Pick<ScenarioRow, "priority_institution_id" | "transcript_id" | "assumptions" | "current_institution_id" | "target_term" | "max_credits" | "residency_status" | "institution_type" | "graduation_target" | "is_archived">>,
      Partial<Omit<ScenarioRow, "id" | "user_id" | "created_at" | "updated_at">>
    >;
    scenario_targets: Table<
      { id: string; scenario_id: string; institution_id: string | null; institution_key: string; program_id: string | null; program_key: string | null; is_priority: boolean; priority: number; created_at: string },
      { id?: string; scenario_id: string; institution_id?: string | null; institution_key: string; program_id?: string | null; program_key?: string | null; is_priority?: boolean; priority?: number },
      { institution_id?: string | null; institution_key?: string; program_id?: string | null; program_key?: string | null; is_priority?: boolean; priority?: number }
    >;
    planned_courses: Table<
      { id: string; scenario_id: string; client_id: string; course_id: string | null; course_code: string; title: string; credits: number; term_id: string; term_label: string; satisfies: string[]; source: string; created_at: string },
      { id?: string; scenario_id: string; client_id: string; course_id?: string | null; course_code: string; title: string; credits: number; term_id: string; term_label: string; satisfies?: string[]; source: string },
      { course_id?: string | null; course_code?: string; title?: string; credits?: number; term_id?: string; term_label?: string; satisfies?: string[]; source?: string }
    >;
    scenario_results: Table<
      { id: string; scenario_id: string; analysis_version: string; source_bundle_hash: string | null; generated_at: string; input_snapshot: Json; eligibility: Json; transferable_credits: number | null; degree_applicable_credits: number | null; estimated_remaining_credits: number | null; estimated_graduation_term: string | null; warnings: Json; unresolved_assumptions: Json; recommended_actions: Json; full_result: Json; created_at: string },
      { id?: string; scenario_id: string; analysis_version: string; source_bundle_hash?: string | null; generated_at: string; input_snapshot: Json; eligibility?: Json; transferable_credits?: number | null; degree_applicable_credits?: number | null; estimated_remaining_credits?: number | null; estimated_graduation_term?: string | null; warnings?: Json; unresolved_assumptions?: Json; recommended_actions?: Json; full_result: Json },
      never
    >;
    advisor_messages: Table<
      { id: string; scenario_id: string; user_id: string; role: "user" | "assistant"; content: string; confidence: ConfidenceLevel | null; citation_ids: string[]; assumptions: Json; created_at: string },
      { id?: string; scenario_id: string; user_id: string; role: "user" | "assistant"; content: string; confidence?: ConfidenceLevel | null; citation_ids?: string[]; assumptions?: Json },
      never
    >;
  }, { verification_status: "confirmed" | "likely" | "unclear" | "manual_evaluation" | "conflicting" }>;
};
