import type { SupabaseClient } from "@supabase/supabase-js";
import type { Database, Json } from "@/lib/supabase/database.types";
import type { PersistedTranscript, SaveTranscriptRequest } from "@/lib/backend/types";

function json(value: unknown): Json {
  return JSON.parse(JSON.stringify(value)) as Json;
}

function splitCourseCode(code: string) {
  const match = code.trim().match(/^(.*?)[\s]+([A-Z0-9-]+)$/i);
  return { subject: match?.[1]?.trim() || null, number: match?.[2]?.trim() || null };
}

export class SupabaseTranscriptRepository {
  constructor(private readonly client: SupabaseClient<Database>, private readonly userId: string) {}

  async save({ transcript, profile }: SaveTranscriptRequest): Promise<PersistedTranscript> {
    const profileResult = await this.client.schema("student").from("profiles").upsert({
      id: this.userId,
      display_name: profile.firstName,
      current_institution_name: profile.currentInstitution,
      institution_type: profile.institutionType,
      residency_status: profile.residency,
      intended_term: profile.targetTransferTerm,
      onboarding_state: json(profile),
    }, { onConflict: "id" });
    if (profileResult.error) throw new Error(`Could not save profile: ${profileResult.error.message}`);

    const transcriptResult = await this.client.schema("student").from("transcripts").upsert({
      user_id: this.userId,
      client_id: transcript.id,
      original_filename: transcript.fileName ?? null,
      extraction_status: transcript.extractionStatus,
      verification_status: transcript.verificationStatus,
      cumulative_gpa: transcript.cumulativeGpa,
      extraction_metadata: json({ source: "pathwise-web", institutions: transcript.institutions }),
    }, { onConflict: "user_id,client_id" }).select("id").single();
    if (transcriptResult.error || !transcriptResult.data) throw new Error(`Could not save transcript: ${transcriptResult.error?.message ?? "No record returned"}`);
    const transcriptId = transcriptResult.data.id;

    const clearCourses = await this.client.schema("student").from("course_records").delete().eq("transcript_id", transcriptId);
    if (clearCourses.error) throw new Error(`Could not refresh transcript courses: ${clearCourses.error.message}`);
    const clearInstitutions = await this.client.schema("student").from("transcript_institutions").delete().eq("transcript_id", transcriptId);
    if (clearInstitutions.error) throw new Error(`Could not refresh transcript institutions: ${clearInstitutions.error.message}`);
    const clearExams = await this.client.schema("student").from("exam_scores").delete().eq("transcript_id", transcriptId);
    if (clearExams.error) throw new Error(`Could not refresh exam scores: ${clearExams.error.message}`);

    const institutionResult = transcript.institutions.length
      ? await this.client.schema("student").from("transcript_institutions").insert(
        transcript.institutions.map((institutionName, index) => ({
          transcript_id: transcriptId,
          institution_name: institutionName,
          is_primary: index === 0,
        })),
      ).select("id,institution_name")
      : { data: [], error: null };
    if (institutionResult.error) throw new Error(`Could not save transcript institutions: ${institutionResult.error.message}`);
    const institutionIds = new Map((institutionResult.data ?? []).map((item) => [item.institution_name, item.id]));

    if (transcript.courses.length) {
      const courseResult = await this.client.schema("student").from("course_records").insert(transcript.courses.map((course) => {
        const code = splitCourseCode(course.code);
        return {
          transcript_id: transcriptId,
          transcript_institution_id: institutionIds.get(course.institution) ?? null,
          client_id: course.id,
          institution_name: course.institution,
          subject: code.subject,
          number: code.number,
          course_code: course.code,
          course_title: course.title,
          term: course.term,
          credits_attempted: course.creditsAttempted,
          credits_earned: course.creditsEarned,
          grade: course.grade,
          course_status: course.status,
          repeat_indicator: course.repeat,
          transfer_indicator: course.transfer,
          in_progress: course.status === "in-progress",
          extraction_confidence: course.confidence,
          user_verified: transcript.verificationStatus === "confirmed",
          extraction_evidence: json({ notes: course.notes ?? null }),
          notes: course.notes ?? null,
        };
      }));
      if (courseResult.error) throw new Error(`Could not save transcript courses: ${courseResult.error.message}`);
    }

    if (transcript.examCredits.length) {
      const examResult = await this.client.schema("student").from("exam_scores").insert(transcript.examCredits.map((exam) => ({
        user_id: this.userId,
        transcript_id: transcriptId,
        client_id: exam.id,
        exam_type: exam.type,
        subject: exam.subject,
        score: exam.score,
        credits_awarded: exam.creditsAwarded,
        enabled: exam.enabled,
        user_verified: transcript.verificationStatus === "confirmed",
      })));
      if (examResult.error) throw new Error(`Could not save exam scores: ${examResult.error.message}`);
    }

    return { id: transcriptId, courseCount: transcript.courses.length, examScoreCount: transcript.examCredits.length };
  }
}
