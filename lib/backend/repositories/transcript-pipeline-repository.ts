import type { SupabaseClient } from "@supabase/supabase-js";
import type { Database, Json } from "@/lib/supabase/database.types";
import type { TranscriptDocumentStatus, TranscriptPipelineResult } from "@/lib/transcript/types";
import { getConfiguredModel } from "@/lib/openai";

function asJson(value: unknown): Json {
  return JSON.parse(JSON.stringify(value)) as Json;
}

function safeFileName(name: string) {
  const cleaned = name.normalize("NFKD").replace(/[^a-zA-Z0-9._-]+/g, "-").replace(/^-+|-+$/g, "");
  return cleaned || "transcript.pdf";
}

export class SupabaseTranscriptPipelineRepository {
  constructor(private readonly client: SupabaseClient<Database>, private readonly userId: string) {}

  async list() {
    const result = await this.client.schema("student").from("transcript_documents").select("*").eq("user_id", this.userId).order("created_at", { ascending: false });
    if (result.error) throw new Error(result.error.message);
    return result.data;
  }

  async findDocument(documentId: string) {
    const result = await this.client.schema("student").from("transcript_documents").select("*").eq("id", documentId).eq("user_id", this.userId).maybeSingle();
    if (result.error) throw new Error(result.error.message);
    return result.data;
  }

  async findDuplicate(contentHash: string) {
    const result = await this.client.schema("student").from("transcript_documents").select("*").eq("user_id", this.userId).eq("content_hash_sha256", contentHash).maybeSingle();
    if (result.error) throw new Error(result.error.message);
    return result.data;
  }

  async upload(file: File, sha256: string) {
    const documentId = crypto.randomUUID();
    const storagePath = `${this.userId}/${documentId}/${safeFileName(file.name)}`;
    const storage = await this.client.storage.from("transcript-uploads").upload(storagePath, file, { contentType: "application/pdf", upsert: false });
    if (storage.error) throw new Error(`Private upload failed: ${storage.error.message}`);
    const result = await this.client.schema("student").from("transcript_documents").insert({
      id: documentId,
      user_id: this.userId,
      original_filename: file.name,
      storage_path: storagePath,
      size_bytes: file.size,
      content_hash_sha256: sha256,
    }).select("*").single();
    if (result.error) {
      await this.client.storage.from("transcript-uploads").remove([storagePath]);
      throw new Error(`Document record failed: ${result.error.message}`);
    }
    return result.data;
  }

  async download(documentId: string) {
    const document = await this.findDocument(documentId);
    if (!document) return null;
    const result = await this.client.storage.from(document.storage_bucket).download(document.storage_path);
    if (result.error) throw new Error(result.error.message);
    return { document, blob: result.data };
  }

  async setStatus(documentId: string, status: TranscriptDocumentStatus, failure?: { code: string; message: string }) {
    const result = await this.client.schema("student").from("transcript_documents").update({
      status,
      failure_code: failure?.code ?? null,
      failure_message: failure?.message ?? null,
    }).eq("id", documentId).eq("user_id", this.userId).select("*").single();
    if (result.error) throw new Error(result.error.message);
    return result.data;
  }

  private async nextRunSequence(documentId: string) {
    const result = await this.client.schema("student").from("transcript_parse_runs").select("sequence_number").eq("document_id", documentId).order("sequence_number", { ascending: false }).limit(1);
    if (result.error) throw new Error(result.error.message);
    return (result.data[0]?.sequence_number ?? 0) + 1;
  }

  async persistPipelineResult(documentId: string, result: TranscriptPipelineResult) {
    const sequence = await this.nextRunSequence(documentId);
    const now = new Date().toISOString();
    const runResult = await this.client.schema("student").from("transcript_parse_runs").insert({
      document_id: documentId,
      sequence_number: sequence,
      parser_name: result.parsedDocument.parser,
      parser_version: result.parsedDocument.parserVersion,
      extraction_model: getConfiguredModel(),
      status: "succeeded",
      raw_parser_output: asJson(result.parsedDocument),
      raw_model_output: asJson(result.validatedTranscript.extraction),
      validation_output: asJson({ warnings: result.validatedTranscript.warnings, metrics: result.validatedTranscript.metrics }),
      started_at: now,
      completed_at: now,
    }).select("id").single();
    if (runResult.error) throw new Error(runResult.error.message);
    const parseRunId = runResult.data.id;

    if (result.parsedDocument.pages.length) {
      const pages = await this.client.schema("student").from("transcript_pages").insert(result.parsedDocument.pages.map((page) => ({
        parse_run_id: parseRunId,
        page_number: page.pageNumber,
        markdown: page.markdown,
        plain_text: page.text,
        parser_blocks: asJson(page.blocks),
      })));
      if (pages.error) throw new Error(pages.error.message);
    }

    await this.clearReviewedExtraction(documentId);
    const extraction = result.validatedTranscript.extraction;
    const institutionResult = await this.client.schema("student").from("student_institutions").insert(extraction.institutions.map((item) => ({
      document_id: documentId, source_entity_id: item.id, institution_name: item.name, student_identifier: item.studentIdentifier,
      attendance_start: item.attendanceStart, attendance_end: item.attendanceEnd, degree_name: item.degreeName, degree_date: item.degreeDate,
      extraction_confidence: item.confidence, source_page: item.source.pageNumber, source_block_ids: asJson(item.source.parserBlockIds), source_raw_text: item.source.rawText,
    }))).select("id,source_entity_id");
    if (institutionResult.error) throw new Error(institutionResult.error.message);
    const institutionIds = new Map(institutionResult.data.map((item) => [item.source_entity_id, item.id]));

    const termResult = await this.client.schema("student").from("academic_terms").insert(extraction.terms.map((item) => ({
      document_id: documentId, student_institution_id: institutionIds.get(item.institutionId)!, source_entity_id: item.id, label: item.label,
      start_date: item.startDate, end_date: item.endDate, academic_level: item.academicLevel, credits_attempted: item.creditsAttempted,
      credits_earned: item.creditsEarned, term_gpa: item.termGpa, extraction_confidence: item.confidence, source_page: item.source.pageNumber,
      source_block_ids: asJson(item.source.parserBlockIds), source_raw_text: item.source.rawText,
    }))).select("id,source_entity_id");
    if (termResult.error) throw new Error(termResult.error.message);
    const termIds = new Map(termResult.data.map((item) => [item.source_entity_id, item.id]));

    if (extraction.courses.length) {
      const courses = await this.client.schema("student").from("transcript_courses").insert(extraction.courses.map((item) => ({
        document_id: documentId, student_institution_id: institutionIds.get(item.institutionId)!, academic_term_id: termIds.get(item.termId)!, source_entity_id: item.id,
        course_code: item.courseCode, course_title: item.courseTitle, credits_attempted: item.creditsAttempted, credits_earned: item.creditsEarned,
        grade: item.grade, course_status: item.status, repeat_indicator: item.repeatIndicator, transfer_indicator: item.transferIndicator,
        extraction_confidence: item.confidence, source_page: item.source.pageNumber, source_block_ids: asJson(item.source.parserBlockIds), source_raw_text: item.source.rawText,
      })));
      if (courses.error) throw new Error(courses.error.message);
    }
    if (extraction.examCredits.length) {
      const exams = await this.client.schema("student").from("exam_credits").insert(extraction.examCredits.map((item) => ({
        document_id: documentId, source_entity_id: item.id, exam_type: item.examType, subject: item.subject, score: item.score,
        credits_awarded: item.creditsAwarded, extraction_confidence: item.confidence, source_page: item.source.pageNumber,
        source_block_ids: asJson(item.source.parserBlockIds), source_raw_text: item.source.rawText,
      })));
      if (exams.error) throw new Error(exams.error.message);
    }
    const summary = extraction.summary;
    const summaryResult = await this.client.schema("student").from("transcript_summaries").insert({
      document_id: documentId, cumulative_gpa: summary.cumulativeGpa, total_credits_attempted: summary.totalCreditsAttempted,
      total_credits_earned: summary.totalCreditsEarned, total_quality_points: summary.totalQualityPoints, degree_name: summary.degreeName,
      degree_date: summary.degreeDate, extraction_confidence: summary.confidence, source_page: summary.source.pageNumber,
      source_block_ids: asJson(summary.source.parserBlockIds), source_raw_text: summary.source.rawText,
    });
    if (summaryResult.error) throw new Error(summaryResult.error.message);

    if (result.validatedTranscript.warnings.length) {
      const warnings = await this.client.schema("student").from("transcript_warnings").insert(result.validatedTranscript.warnings.map((item) => ({
        document_id: documentId, parse_run_id: parseRunId, client_warning_id: item.id, warning_code: item.code, severity: item.severity,
        state: item.state, entity_type: item.entityType, entity_source_id: item.entityId, message: item.message, details: asJson(item.details),
        source_page: item.source?.pageNumber ?? null, source_block_ids: asJson(item.source?.parserBlockIds ?? []),
      })));
      if (warnings.error) throw new Error(warnings.error.message);
    }

    const status = result.validatedTranscript.requiresReview ? "needs_review" : "completed";
    const documentUpdate = await this.client.schema("student").from("transcript_documents").update({ status, active_parse_run_id: parseRunId, failure_code: null, failure_message: null }).eq("id", documentId).eq("user_id", this.userId).select("*").single();
    if (documentUpdate.error) throw new Error(documentUpdate.error.message);
    return documentUpdate.data;
  }

  async persistFailure(documentId: string, parserName: string, error: Error) {
    const sequence = await this.nextRunSequence(documentId);
    const now = new Date().toISOString();
    const run = await this.client.schema("student").from("transcript_parse_runs").insert({
      document_id: documentId, sequence_number: sequence, parser_name: parserName, parser_version: "unknown", status: "failed",
      error_code: "pipeline_failed", error_message: error.message, started_at: now, completed_at: now,
    });
    if (run.error) throw new Error(run.error.message);
    return this.setStatus(documentId, "failed", { code: "pipeline_failed", message: error.message });
  }

  private async clearReviewedExtraction(documentId: string) {
    for (const table of ["transcript_warnings", "transcript_courses", "exam_credits", "transcript_summaries", "academic_terms", "student_institutions"] as const) {
      const result = await this.client.schema("student").from(table).delete().eq("document_id", documentId);
      if (result.error) throw new Error(result.error.message);
    }
  }

  async getDetailed(documentId: string) {
    const document = await this.findDocument(documentId);
    if (!document) return null;
    const [runs, pages, institutions, terms, courses, exams, summary, warnings, actions] = await Promise.all([
      this.client.schema("student").from("transcript_parse_runs").select("id,sequence_number,parser_name,parser_version,extraction_model,status,error_code,error_message,created_at").eq("document_id", documentId).order("sequence_number", { ascending: false }),
      document.active_parse_run_id ? this.client.schema("student").from("transcript_pages").select("*").eq("parse_run_id", document.active_parse_run_id).order("page_number") : Promise.resolve({ data: [], error: null }),
      this.client.schema("student").from("student_institutions").select("*").eq("document_id", documentId).order("created_at"),
      this.client.schema("student").from("academic_terms").select("*").eq("document_id", documentId).order("created_at"),
      this.client.schema("student").from("transcript_courses").select("*").eq("document_id", documentId).order("created_at"),
      this.client.schema("student").from("exam_credits").select("*").eq("document_id", documentId).order("created_at"),
      this.client.schema("student").from("transcript_summaries").select("*").eq("document_id", documentId).maybeSingle(),
      this.client.schema("student").from("transcript_warnings").select("*").eq("document_id", documentId).order("created_at"),
      this.client.schema("student").from("transcript_review_actions").select("*").eq("document_id", documentId).order("created_at", { ascending: false }),
    ]);
    const failed = [runs, pages, institutions, terms, courses, exams, summary, warnings, actions].find((item) => item.error);
    if (failed?.error) throw new Error(failed.error.message);
    return { document, runs: runs.data, pages: pages.data, institutions: institutions.data, terms: terms.data, courses: courses.data, examCredits: exams.data, summary: summary.data, warnings: warnings.data, reviewActions: actions.data };
  }

  async updateCourse(documentId: string, courseId: string, patch: Record<string, unknown>) {
    const allowed = ["student_institution_id", "academic_term_id", "course_code", "course_title", "credits_attempted", "credits_earned", "grade", "course_status", "repeat_indicator", "transfer_indicator"];
    const update = Object.fromEntries(Object.entries(patch).filter(([key]) => allowed.includes(key)));
    const before = await this.client.schema("student").from("transcript_courses").select("*").eq("id", courseId).eq("document_id", documentId).single();
    if (before.error) throw new Error(before.error.message);
    const result = await this.client.schema("student").from("transcript_courses").update({ ...update, user_verified: true }).eq("id", courseId).eq("document_id", documentId).select("*").single();
    if (result.error) throw new Error(result.error.message);
    await this.reviewAction(documentId, "update", "course", courseId, null, before.data, result.data);
    return result.data;
  }

  async addCourse(documentId: string, input: Record<string, unknown>) {
    const result = await this.client.schema("student").from("transcript_courses").insert({
      document_id: documentId,
      student_institution_id: String(input.student_institution_id), academic_term_id: String(input.academic_term_id), source_entity_id: crypto.randomUUID(),
      course_code: String(input.course_code ?? ""), course_title: String(input.course_title ?? ""), credits_attempted: Number(input.credits_attempted ?? 0),
      credits_earned: Number(input.credits_earned ?? 0), grade: input.grade == null ? null : String(input.grade), course_status: String(input.course_status ?? "unknown"),
      extraction_confidence: 1, source_page: Number(input.source_page ?? 1), source_block_ids: [], source_raw_text: "User-added course", user_verified: true,
    }).select("*").single();
    if (result.error) throw new Error(result.error.message);
    await this.reviewAction(documentId, "add", "course", result.data.id, null, null, result.data);
    return result.data;
  }

  async deleteCourse(documentId: string, courseId: string) {
    const before = await this.client.schema("student").from("transcript_courses").select("*").eq("id", courseId).eq("document_id", documentId).single();
    if (before.error) throw new Error(before.error.message);
    const result = await this.client.schema("student").from("transcript_courses").delete().eq("id", courseId).eq("document_id", documentId);
    if (result.error) throw new Error(result.error.message);
    await this.reviewAction(documentId, "delete", "course", courseId, null, before.data, null);
  }

  async addExamCredit(documentId: string, input: Record<string, unknown>) {
    const result = await this.client.schema("student").from("exam_credits").insert({
      document_id: documentId, source_entity_id: crypto.randomUUID(), exam_type: String(input.exam_type ?? "other"), subject: String(input.subject ?? ""),
      score: input.score == null ? null : String(input.score), credits_awarded: Number(input.credits_awarded ?? 0), extraction_confidence: 1,
      source_page: Number(input.source_page ?? 1), source_block_ids: [], source_raw_text: "User-added exam credit", user_verified: true,
    }).select("*").single();
    if (result.error) throw new Error(result.error.message);
    await this.reviewAction(documentId, "add", "exam_credit", result.data.id, null, null, result.data);
    return result.data;
  }

  async resolveWarning(documentId: string, warningId: string, state: "resolved" | "dismissed", note?: string) {
    const result = await this.client.schema("student").from("transcript_warnings").update({ state, resolution_note: note ?? null, resolved_at: new Date().toISOString() }).eq("id", warningId).eq("document_id", documentId).select("*").single();
    if (result.error) throw new Error(result.error.message);
    await this.reviewAction(documentId, state, "warning", warningId, null, null, result.data);
    return result.data;
  }

  async confirm(documentId: string) {
    const blocking = await this.client.schema("student").from("transcript_warnings").select("id").eq("document_id", documentId).eq("severity", "blocking").eq("state", "open");
    if (blocking.error) throw new Error(blocking.error.message);
    if (blocking.data.length) throw new Error("Resolve all blocking warnings before confirming the transcript.");
    for (const table of ["student_institutions", "academic_terms", "transcript_courses", "exam_credits", "transcript_summaries"] as const) {
      const result = await this.client.schema("student").from(table).update({ user_verified: true }).eq("document_id", documentId);
      if (result.error) throw new Error(result.error.message);
    }
    const result = await this.client.schema("student").from("transcript_documents").update({ status: "completed", confirmed_at: new Date().toISOString() }).eq("id", documentId).eq("user_id", this.userId).select("*").single();
    if (result.error) throw new Error(result.error.message);
    await this.reviewAction(documentId, "confirm", "document", documentId, null, null, { status: "completed" });
    return result.data;
  }

  async deleteDocument(documentId: string) {
    const document = await this.findDocument(documentId);
    if (!document) return false;
    const storage = await this.client.storage.from(document.storage_bucket).remove([document.storage_path]);
    if (storage.error) throw new Error(storage.error.message);
    const result = await this.client.schema("student").from("transcript_documents").delete().eq("id", documentId).eq("user_id", this.userId);
    if (result.error) throw new Error(result.error.message);
    return true;
  }

  private async reviewAction(documentId: string, actionType: string, entityType: string, entityId: string | null, fieldName: string | null, previousValue: unknown, newValue: unknown) {
    const result = await this.client.schema("student").from("transcript_review_actions").insert({
      document_id: documentId, user_id: this.userId, action_type: actionType, entity_type: entityType, entity_id: entityId,
      field_name: fieldName, previous_value: previousValue == null ? null : asJson(previousValue), new_value: newValue == null ? null : asJson(newValue),
    });
    if (result.error) throw new Error(result.error.message);
  }
}
