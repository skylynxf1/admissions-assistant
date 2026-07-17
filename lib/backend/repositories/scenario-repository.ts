import type { SupabaseClient } from "@supabase/supabase-js";
import type { Database, Json } from "@/lib/supabase/database.types";
import type { PersistedScenario, SaveScenarioRequest } from "@/lib/backend/types";

const schoolSlugs: Record<string, string> = { uw: "uw-seattle", berkeley: "uc-berkeley", ucla: "ucla" };

function json(value: unknown): Json {
  return JSON.parse(JSON.stringify(value)) as Json;
}

export class SupabaseScenarioRepository {
  constructor(
    private readonly userClient: SupabaseClient<Database>,
    private readonly userId: string,
    private readonly adminClient: SupabaseClient<Database> | null,
  ) {}

  async list() {
    const { data, error } = await this.userClient.schema("planning").from("scenarios")
      .select("id,client_id,name,planning_mode,updated_at,is_archived")
      .eq("is_archived", false)
      .order("updated_at", { ascending: false })
      .limit(50);
    if (error) throw new Error(`Could not list scenarios: ${error.message}`);
    return data;
  }

  async save(request: SaveScenarioRequest): Promise<PersistedScenario> {
    const clientId = request.clientId ?? "active-transfer-plan";
    const prioritySlug = request.prioritySchoolId ? schoolSlugs[request.prioritySchoolId] : null;
    const selectedSlugs = [...new Set(request.input.targets.map((target) => schoolSlugs[target.schoolId]).filter(Boolean))];
    const institutionLookup = selectedSlugs.length
      ? await this.userClient.schema("catalog").from("institutions").select("id,slug").in("slug", selectedSlugs)
      : { data: [], error: null };
    if (institutionLookup.error) throw new Error(`Could not resolve target institutions: ${institutionLookup.error.message}`);
    const institutionIds = new Map((institutionLookup.data ?? []).map((item) => [item.slug, item.id]));

    const currentInstitutionLookup = await this.userClient.schema("catalog").from("institutions")
      .select("id")
      .ilike("name", request.input.scenario.currentInstitution)
      .limit(1)
      .maybeSingle();
    if (currentInstitutionLookup.error) throw new Error(`Could not resolve current institution: ${currentInstitutionLookup.error.message}`);
    const currentInstitutionId = currentInstitutionLookup.data?.id ?? null;

    const selectedProgramSlugs = [...new Set(request.input.targets.flatMap((target) =>
      target.majorIds.map((majorId) => majorId.startsWith(`${target.schoolId}-`) ? majorId.slice(target.schoolId.length + 1) : majorId),
    ))];
    const programLookup = selectedProgramSlugs.length
      ? await this.userClient.schema("catalog").from("programs").select("id,institution_id,slug").in("slug", selectedProgramSlugs)
      : { data: [], error: null };
    if (programLookup.error) throw new Error(`Could not resolve target programs: ${programLookup.error.message}`);
    const programIds = new Map((programLookup.data ?? []).map((item) => [`${item.institution_id}:${item.slug}`, item.id]));

    let priorityInstitutionId: string | null = null;
    if (prioritySlug) priorityInstitutionId = institutionIds.get(prioritySlug) ?? null;

    const profileResult = await this.userClient.schema("student").from("profiles").upsert({
      id: this.userId,
      display_name: request.input.profile.firstName,
      current_institution_id: currentInstitutionId,
      current_institution_name: request.input.profile.currentInstitution,
      institution_type: request.input.profile.institutionType,
      residency_status: request.input.profile.residency,
      intended_term: request.input.profile.targetTransferTerm,
      onboarding_state: json(request.input.profile),
    }, { onConflict: "id" });
    if (profileResult.error) throw new Error(`Could not save profile: ${profileResult.error.message}`);

    const scenarioResult = await this.userClient.schema("planning").from("scenarios").upsert({
      user_id: this.userId,
      client_id: clientId,
      name: request.name ?? "My transfer plan",
      planning_mode: request.planningMode ?? "transfer",
      priority_institution_id: priorityInstitutionId,
      current_institution_id: currentInstitutionId,
      target_term: request.input.scenario.targetTransferTerm,
      max_credits: request.input.scenario.preferredCreditLoad,
      residency_status: request.input.scenario.residency,
      institution_type: request.input.scenario.institutionType,
      graduation_target: request.input.scenario.graduationTarget,
      profile_snapshot: json(request.input.profile),
      settings: json(request.input.scenario),
      assumptions: json({ selectedTargets: request.input.targets }),
    }, { onConflict: "user_id,client_id" }).select("id,updated_at").single();
    if (scenarioResult.error || !scenarioResult.data) throw new Error(`Could not save scenario: ${scenarioResult.error?.message ?? "No record returned"}`);
    const scenarioId = scenarioResult.data.id;

    const clearTargets = await this.userClient.schema("planning").from("scenario_targets").delete().eq("scenario_id", scenarioId);
    if (clearTargets.error) throw new Error(`Could not refresh scenario targets: ${clearTargets.error.message}`);
    const targetRows: Database["planning"]["Tables"]["scenario_targets"]["Insert"][] = [];
    request.input.targets.forEach((target, targetIndex) => {
      const institutionId = institutionIds.get(schoolSlugs[target.schoolId]) ?? null;
      const targetPriority = target.schoolId === request.prioritySchoolId ? 1 : targetIndex + 2;
      if (target.majorIds.length === 0) {
        targetRows.push({ scenario_id: scenarioId, institution_id: institutionId, institution_key: target.schoolId, program_key: null, is_priority: target.schoolId === request.prioritySchoolId, priority: targetPriority });
        return;
      }
      target.majorIds.forEach((majorId) => {
        const programSlug = majorId.startsWith(`${target.schoolId}-`) ? majorId.slice(target.schoolId.length + 1) : majorId;
        targetRows.push({
          scenario_id: scenarioId,
          institution_id: institutionId,
          institution_key: target.schoolId,
          program_id: institutionId ? programIds.get(`${institutionId}:${programSlug}`) ?? null : null,
          program_key: majorId,
          is_priority: target.schoolId === request.prioritySchoolId,
          priority: targetPriority,
        });
      });
    });
    if (targetRows.length) {
      const targetsResult = await this.userClient.schema("planning").from("scenario_targets").insert(targetRows);
      if (targetsResult.error) throw new Error(`Could not save scenario targets: ${targetsResult.error.message}`);
    }

    const clearCourses = await this.userClient.schema("planning").from("planned_courses").delete().eq("scenario_id", scenarioId);
    if (clearCourses.error) throw new Error(`Could not refresh planned courses: ${clearCourses.error.message}`);
    if (request.input.scenario.plannedCourses.length) {
      const coursesResult = await this.userClient.schema("planning").from("planned_courses").insert(
        request.input.scenario.plannedCourses.map((course) => ({
          scenario_id: scenarioId,
          client_id: course.id,
          course_code: course.course,
          title: course.title,
          credits: course.credits,
          term_id: course.termId,
          term_label: course.termLabel,
          satisfies: course.satisfies,
          source: course.source,
        })),
      );
      if (coursesResult.error) throw new Error(`Could not save planned courses: ${coursesResult.error.message}`);
    }

    let resultId: string | null = null;
    if (request.analysis && this.adminClient) {
      const insertedResult = await this.adminClient.schema("planning").from("scenario_results").insert({
        scenario_id: scenarioId,
        analysis_version: "mock-v1",
        generated_at: request.analysis.generatedAt,
        input_snapshot: json(request.input),
        eligibility: json(request.analysis.readiness),
        transferable_credits: request.analysis.creditSummary.estimatedTransferable,
        degree_applicable_credits: request.analysis.creditSummary.degreeApplicable,
        estimated_remaining_credits: request.analysis.simulationSummary.estimatedRemainingCredits,
        estimated_graduation_term: request.analysis.simulationSummary.estimatedGraduationTerm,
        warnings: json(request.analysis.alerts),
        unresolved_assumptions: json(request.analysis.verifications.filter((item) => item.status !== "confirmed")),
        recommended_actions: json(request.analysis.recommendations),
        full_result: json(request.analysis),
      }).select("id").single();
      if (insertedResult.error || !insertedResult.data) throw new Error(`Could not save scenario result: ${insertedResult.error?.message ?? "No record returned"}`);
      resultId = insertedResult.data.id;
    }

    return { id: scenarioId, resultId, updatedAt: scenarioResult.data.updated_at };
  }
}
