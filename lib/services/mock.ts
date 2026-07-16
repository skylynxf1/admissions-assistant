import { createSampleTranscript } from "@/data/sample-transcript";
import { getMajor, getSchool, sampleCitations, schoolCatalog } from "@/data/sample-policies";
import type {
  AcademicAnalysisInput,
  AdvisorAnswer,
  AdvisorInput,
  AnalysisAlert,
  AnalysisResult,
  CourseEquivalency,
  CourseRecord,
  CourseRecommendation,
  CreditSummary,
  DraftEmail,
  PrerequisiteChain,
  ProgramReadiness,
  RequirementResult,
  RequirementState,
  SchoolDefinition,
  SimulationSummary,
  TranscriptData,
  VerificationItem,
} from "@/lib/types";
import type {
  AcademicRecordNormalizer,
  AdvisorChatService,
  CourseRecommendationEngine,
  EquivalencyAnalyzer,
  PolicyRetrievalService,
  PrerequisiteGraphService,
  RequirementEvaluator,
  ScenarioSimulator,
  TranscriptParser,
  UncertaintyEscalationHandler,
  VerificationEvaluator,
} from "@/lib/services/interfaces";

const clamp = (value: number, min: number, max: number) => Math.min(Math.max(value, min), max);

const gradePoints: Record<string, number> = {
  A: 4, "A-": 3.7, "B+": 3.3, B: 3, "B-": 2.7, "C+": 2.3, C: 2,
  "C-": 1.7, "D+": 1.3, D: 1, F: 0,
};

function calculateProjectedGpa(transcript: TranscriptData) {
  const graded = transcript.courses.filter((course) => course.status === "completed" && gradePoints[course.grade.toUpperCase()] !== undefined);
  const qualityPoints = graded.reduce((sum, course) => sum + gradePoints[course.grade.toUpperCase()] * Math.max(course.creditsAttempted, 1), 0);
  const gradedCredits = graded.reduce((sum, course) => sum + Math.max(course.creditsAttempted, 1), 0);
  return gradedCredits ? Math.round((qualityPoints / gradedCredits) * 100) / 100 : transcript.cumulativeGpa;
}

function isPassing(course: CourseRecord) {
  const points = gradePoints[course.grade.toUpperCase()];
  return course.status === "completed" && (points === undefined || points >= 1.7);
}

function targetPairs(input: AcademicAnalysisInput) {
  return input.targets.flatMap((target) =>
    target.majorIds.map((majorId) => ({ schoolId: target.schoolId, majorId })),
  );
}

function calculateCreditSummary(input: AcademicAnalysisInput): CreditSummary {
  const completed = input.transcript.courses.filter(isPassing);
  const earned = completed.reduce((sum, course) => sum + course.creditsEarned, 0);
  const attempted = input.transcript.courses.reduce((sum, course) => sum + course.creditsAttempted, 0);
  const inProgress = input.transcript.courses
    .filter((course) => course.status === "in-progress")
    .reduce((sum, course) => sum + course.creditsAttempted, 0);
  const examCredits = input.scenario.useExamCredit
    ? input.transcript.examCredits.filter((credit) => credit.enabled).reduce((sum, credit) => sum + credit.creditsAwarded, 0)
    : 0;
  const plannedCredits = input.scenario.plannedCourses.reduce((sum, course) => sum + course.credits, 0);
  const uncertainPenalty = completed.filter((course) => course.confidence !== "high").length * 1.5;
  const estimatedTransferable = Math.round((earned + inProgress * 0.85 + plannedCredits * 0.9 + examCredits - uncertainPenalty) * 10) / 10;
  const institutionPenalty = input.scenario.institutionType.includes("four-year") ? 6 : 3;
  const degreeApplicable = Math.max(0, estimatedTransferable - institutionPenalty);
  const majorApplicable = Math.max(0, Math.min(degreeApplicable, 25 + targetPairs(input).length * 2));

  return {
    attempted,
    earned,
    estimatedTransferable,
    degreeApplicable,
    majorApplicable,
    inProgress,
    examCredits,
    electiveOnly: Math.max(0, Math.round((estimatedTransferable - degreeApplicable) * 10) / 10),
  };
}

// MOCK IMPLEMENTATION: replace with GPT-5.6 structured transcript extraction.
export class MockTranscriptParser implements TranscriptParser {
  async parse(fileName?: string): Promise<TranscriptData> {
    const transcript = createSampleTranscript();
    return { ...transcript, fileName: fileName ?? transcript.fileName };
  }
}

// MOCK IMPLEMENTATION: production normalization should be deterministic and audit repeated/duplicate credit.
export class MockAcademicRecordNormalizer implements AcademicRecordNormalizer {
  async normalize(courses: CourseRecord[]): Promise<CourseRecord[]> {
    return courses.map((course) => ({
      ...course,
      code: course.code.trim().toUpperCase(),
      title: course.title.trim(),
      creditsEarned: Math.min(course.creditsEarned, course.creditsAttempted),
    }));
  }
}

// MOCK IMPLEMENTATION: replace with retrieval over official, versioned university sources.
export class MockPolicyRetrievalService implements PolicyRetrievalService {
  async retrieve(input: AcademicAnalysisInput): Promise<SchoolDefinition[]> {
    return schoolCatalog.filter((school) => input.targets.some((target) => target.schoolId === school.id));
  }
}

// MOCK IMPLEMENTATION: examples are intentionally marked with confidence and sample citations.
export class MockEquivalencyAnalyzer implements EquivalencyAnalyzer {
  async analyze(input: AcademicAnalysisInput): Promise<CourseEquivalency[]> {
    const selectedSchools = new Set(input.targets.map((target) => target.schoolId));
    const templates: CourseEquivalency[] = [
      {
        id: "eq-math151-uw",
        sourceCourse: "MATH& 151",
        sourceInstitution: "Bellevue College",
        destinationSchoolId: "uw",
        destinationCourse: "MATH 124",
        category: "Quantitative / major prerequisite",
        result: "Appears to be a direct equivalent in the sample mapping.",
        confidence: "high",
        reasoning: "Course title, credit amount, and the sample equivalency record align.",
        confirmationRecommended: false,
        citationIds: ["uw-equivalency"],
      },
      {
        id: "eq-engl101-uw",
        sourceCourse: "ENGL& 101",
        sourceInstitution: "Bellevue College",
        destinationSchoolId: "uw",
        destinationCourse: "No exact course number stored",
        category: "Writing",
        result: "Likely satisfies one composition requirement in this demo.",
        confidence: "high",
        reasoning: "The fictional student record matches the sample writing rule.",
        confirmationRecommended: false,
        citationIds: ["uw-transfer"],
      },
      {
        id: "eq-cs141-uw",
        sourceCourse: "CS 141",
        sourceInstitution: "Bellevue College",
        destinationSchoolId: "uw",
        destinationCourse: "No verified course mapping",
        category: "Major prerequisite",
        result: "No course equivalency is stored; department evaluation is required.",
        confidence: "medium",
        reasoning: "The sample public mapping does not resolve the department-level prerequisite use.",
        confirmationRecommended: true,
        citationIds: ["uw-equivalency", "uw-info"],
      },
      {
        id: "eq-math151-berkeley",
        sourceCourse: "MATH& 151",
        sourceInstitution: "Bellevue College",
        destinationSchoolId: "berkeley",
        destinationCourse: "No verified course mapping",
        category: "Quantitative / major prerequisite",
        result: "No course equivalency is stored; transfer and major applicability are unresolved.",
        confidence: "medium",
        reasoning: "This demo does not contain an official cross-state articulation agreement.",
        confirmationRecommended: true,
        citationIds: ["berkeley-transfer", "berkeley-data"],
      },
      {
        id: "eq-econ201-berkeley",
        sourceCourse: "ECON& 201",
        sourceInstitution: "Bellevue College",
        destinationSchoolId: "berkeley",
        destinationCourse: "No verified course mapping",
        category: "Social science",
        result: "No exact transfer-credit or requirement result is stored.",
        confidence: "medium",
        reasoning: "Subject area aligns; direct articulation is not present in the sample dataset.",
        confirmationRecommended: true,
        citationIds: ["berkeley-transfer"],
      },
      {
        id: "eq-socw-ucla",
        sourceCourse: "SOCW 2010",
        sourceInstitution: "Seattle University",
        destinationSchoolId: "ucla",
        destinationCourse: "No verified course mapping",
        category: "Social science / diversity",
        result: "No exact transfer-credit or requirement result is stored.",
        confidence: "low",
        reasoning: "No direct fictional equivalency is available for this private-school course.",
        confirmationRecommended: true,
        citationIds: ["ucla-transfer"],
      },
    ];

    return templates.filter((item) => selectedSchools.has(item.destinationSchoolId));
  }
}

// MOCK IMPLEMENTATION: every conclusion is limited to an explicit saved sample record.
// A destination course is never inferred when the stored sources do not name one.
export class MockVerificationEvaluator implements VerificationEvaluator {
  async evaluate(input: AcademicAnalysisInput, equivalencies: CourseEquivalency[]): Promise<VerificationItem[]> {
    const selectedSchools = new Set(input.targets.map((target) => target.schoolId));
    const course = (code: string, institution?: string) => input.transcript.courses.find(
      (item) => item.code.toUpperCase() === code.toUpperCase()
        && (!institution || item.institution === institution),
    );
    const buildContext = (code: string, institution?: string) => {
      const match = course(code, institution);
      return {
        sourceCourse: match?.code ?? code,
        sourceInstitution: match?.institution ?? institution ?? input.scenario.currentInstitution,
        sourceTerm: match?.term ?? "Term not found in reviewed record",
      };
    };
    const storedDestination = (id: string) => {
      const match = equivalencies.find((item) => item.id === id);
      return match && !match.destinationCourse.startsWith("No ") ? match.destinationCourse : undefined;
    };

    const items: VerificationItem[] = [];
    if (selectedSchools.has("uw")) {
      items.push(
        {
          id: "verify-math151-uw",
          status: "confirmed",
          title: "Calculus mapping is present in the saved record",
          conclusion: "The saved sample equivalency record explicitly maps this course to UW MATH 124.",
          explanation: "Confirmed means the exact mapping exists in the currently saved source record. The record is still sample, unverified demo data—not live official guidance.",
          ...buildContext("MATH& 151", "Bellevue College"),
          destinationSchoolId: "uw",
          destinationCourse: storedDestination("eq-math151-uw"),
          question: "Does MATH& 151 from Bellevue College satisfy UW MATH 124 for my selected transfer major?",
          office: "Transfer credit office",
          sourceChecks: [{ citationId: "uw-equivalency", outcome: "supports", note: "The saved sample table contains the exact MATH& 151 to MATH 124 mapping." }],
          canDraftEmail: false,
        },
        {
          id: "verify-engl101-uw",
          status: "likely",
          title: "Composition category appears supported",
          conclusion: "The saved writing policy appears to support composition credit, but it does not store an exact UW course number.",
          explanation: "The category rule and transcript subject align. Because no direct course-to-course mapping is saved, the system does not name one.",
          ...buildContext("ENGL& 101", "Bellevue College"),
          destinationSchoolId: "uw",
          question: "Will ENGL& 101 from Bellevue College satisfy the composition requirement for my selected UW transfer major?",
          office: "Admissions",
          sourceChecks: [{ citationId: "uw-transfer", outcome: "supports", note: "The saved policy describes composition credit, but not an exact destination course number." }],
          canDraftEmail: true,
        },
        {
          id: "verify-cs141-uw",
          status: "manual-evaluation",
          title: "Programming course needs department review",
          conclusion: "No UW course equivalency is stored for CS 141. A department must evaluate it before it is used as a major prerequisite.",
          explanation: "The equivalency guide does not resolve this course, while the major policy only identifies the prerequisite area. A syllabus-level evaluation is required.",
          ...buildContext("CS 141", "Bellevue College"),
          destinationSchoolId: "uw",
          question: "Does CS 141 (Computer Science I) from Bellevue College satisfy the introductory programming prerequisite for my selected UW major, or only transfer as elective credit?",
          office: "Department advisor",
          sourceChecks: [
            { citationId: "uw-equivalency", outcome: "does-not-address", note: "No exact CS 141 destination mapping is present in the saved equivalency record." },
            { citationId: "uw-info", outcome: "does-not-address", note: "The major record describes the prerequisite but does not evaluate this source course." },
          ],
          canDraftEmail: true,
        },
      );
    }

    if (selectedSchools.has("berkeley")) {
      items.push(
        {
          id: "verify-econ201-berkeley",
          status: "unclear",
          title: "Economics course use is not documented",
          conclusion: "The checked sources do not provide an exact Berkeley equivalency or a major-applicability decision.",
          explanation: "Subject similarity is not enough to establish transfer or requirement credit, so no destination course has been assigned.",
          ...buildContext("ECON& 201", "Bellevue College"),
          destinationSchoolId: "berkeley",
          question: "How would ECON& 201 from Bellevue College be evaluated for transfer credit and for my selected UC Berkeley major?",
          office: "Transfer credit office",
          sourceChecks: [
            { citationId: "berkeley-transfer", outcome: "does-not-address", note: "The saved transfer policy is general and does not list this course." },
            { citationId: "berkeley-data", outcome: "does-not-address", note: "The saved major record does not identify this source course." },
          ],
          canDraftEmail: true,
        },
        {
          id: "verify-math151-berkeley",
          status: "conflicting",
          title: "General transfer and major-use signals differ",
          conclusion: "One saved record supports possible general transferability, while the major record does not confirm prerequisite use.",
          explanation: "These records answer different questions and cannot be reconciled into a direct equivalency. No Berkeley course number has been assigned.",
          ...buildContext("MATH& 151", "Bellevue College"),
          destinationSchoolId: "berkeley",
          question: "Can MATH& 151 from Bellevue College satisfy the calculus prerequisite for my selected UC Berkeley major, and if not, how will it transfer?",
          office: "Department advisor",
          sourceChecks: [
            { citationId: "berkeley-transfer", outcome: "supports", note: "The general transfer record supports review for transferable quantitative credit." },
            { citationId: "berkeley-data", outcome: "conflicts", note: "The major record does not confirm that this course satisfies the calculus prerequisite." },
          ],
          canDraftEmail: true,
        },
      );
    }

    if (selectedSchools.has("ucla")) {
      items.push({
        id: "verify-socw-ucla",
        status: "manual-evaluation",
        title: "Private-university course needs manual evaluation",
        conclusion: "No UCLA equivalency is stored for this course.",
        explanation: "The saved source contains no direct mapping for this institution and course. The system leaves the destination course blank.",
        ...buildContext("SOCW 2010", "Seattle University"),
        destinationSchoolId: "ucla",
        question: "How will SOCW 2010 from Seattle University be evaluated for UCLA transfer credit and requirement applicability?",
        office: "Transfer credit office",
        sourceChecks: [{ citationId: "ucla-transfer", outcome: "does-not-address", note: "The saved transfer policy does not list this exact course." }],
        canDraftEmail: true,
      });
    }

    return items;
  }
}

function requirementState(complete: boolean, uncertain = false): RequirementState {
  if (uncertain) return "uncertain";
  return complete ? "complete" : "missing";
}

// MOCK IMPLEMENTATION: production evaluation should combine deterministic rules with GPT interpretation.
export class MockRequirementEvaluator implements RequirementEvaluator {
  async evaluate(input: AcademicAnalysisInput, equivalencies: CourseEquivalency[]): Promise<RequirementResult[]> {
    const credits = calculateCreditSummary(input);
    const completedCodes = new Set(input.transcript.courses.filter(isPassing).map((course) => course.code.toUpperCase()));
    const plannedCodes = new Set([
      ...input.transcript.courses.filter((course) => course.status === "in-progress").map((course) => course.code.toUpperCase()),
      ...input.scenario.plannedCourses.map((course) => course.course.toUpperCase()),
    ]);
    const hasCompleted = (code: string) => completedCodes.has(code.toUpperCase());
    const hasPlanned = (code: string) => plannedCodes.has(code.toUpperCase());
    const stateFor = (codes: string[]): RequirementState => codes.every(hasCompleted)
      ? "complete"
      : codes.every((code) => hasCompleted(code) || hasPlanned(code))
        ? "in-progress"
        : "missing";

    return targetPairs(input).flatMap(({ schoolId, majorId }) => {
      const school = getSchool(schoolId);
      const programmingUncertain = equivalencies.some(
        (equivalency) => equivalency.destinationSchoolId === schoolId && equivalency.sourceCourse === "CS 141" && equivalency.confirmationRecommended,
      );
      const minimum = school?.minimumTransferCredits ?? 60;
      return [
        {
          id: `${majorId}-credit-minimum`, schoolId, majorId, category: "Transfer eligibility", title: `${minimum}-credit transfer minimum`,
          state: requirementState(credits.estimatedTransferable >= minimum), completedCredits: Math.min(credits.estimatedTransferable, minimum), requiredCredits: minimum,
          matchedCourses: [], missingCourses: credits.estimatedTransferable >= minimum ? [] : [`${Math.ceil(minimum - credits.estimatedTransferable)} more transferable credits`],
          confidence: "medium", citationIds: [schoolId === "uw" ? "uw-transfer" : schoolId === "berkeley" ? "berkeley-transfer" : "ucla-transfer"],
        },
        {
          id: `${majorId}-writing`, schoolId, majorId, category: "General education", title: "College composition",
          state: stateFor(["ENGL& 101"]), completedCredits: hasCompleted("ENGL& 101") ? 5 : hasPlanned("ENGL& 101") || hasPlanned("ENGL& 102") ? 2.5 : 0, requiredCredits: 5,
          matchedCourses: hasCompleted("ENGL& 101") ? ["ENGL& 101"] : hasPlanned("ENGL& 102") ? ["ENGL& 102 (planned)"] : [], missingCourses: hasCompleted("ENGL& 101") || hasPlanned("ENGL& 102") ? [] : ["College composition"],
          confidence: schoolId === "uw" ? "high" : "medium", citationIds: [schoolId === "uw" ? "uw-transfer" : schoolId === "berkeley" ? "berkeley-transfer" : "ucla-transfer"],
        },
        {
          id: `${majorId}-communication`, schoolId, majorId, category: "General education", title: "Oral communication",
          state: stateFor(["CMST& 220"]), completedCredits: hasCompleted("CMST& 220") ? 5 : hasPlanned("CMST& 220") ? 2.5 : 0, requiredCredits: 5,
          matchedCourses: hasCompleted("CMST& 220") ? ["CMST& 220"] : [], missingCourses: hasCompleted("CMST& 220") || hasPlanned("CMST& 220") ? [] : ["Public speaking"],
          confidence: "medium", citationIds: [schoolId === "uw" ? "uw-transfer" : schoolId === "berkeley" ? "berkeley-transfer" : "ucla-transfer"],
        },
        {
          id: `${majorId}-science`, schoolId, majorId, category: "General education", title: "Natural or lab science",
          state: stateFor(["PHYS& 114"]), completedCredits: hasCompleted("PHYS& 114") ? 5 : hasPlanned("PHYS& 114") ? 2.5 : 0, requiredCredits: 5,
          matchedCourses: hasCompleted("PHYS& 114") ? ["PHYS& 114"] : hasPlanned("PHYS& 114") ? ["PHYS& 114 (planned)"] : [], missingCourses: hasCompleted("PHYS& 114") || hasPlanned("PHYS& 114") ? [] : ["Lab science"],
          confidence: "medium", citationIds: [schoolId === "uw" ? "uw-transfer" : schoolId === "berkeley" ? "berkeley-transfer" : "ucla-transfer"],
        },
        {
          id: `${majorId}-calculus`, schoolId, majorId, category: "Major prerequisite", title: "Calculus sequence",
          state: stateFor(["MATH& 151", "MATH& 152"]),
          completedCredits: ["MATH& 151", "MATH& 152"].reduce((sum, code) => sum + (hasCompleted(code) ? 5 : hasPlanned(code) ? 2.5 : 0), 0),
          requiredCredits: 10, matchedCourses: ["MATH& 151", "MATH& 152"].filter((code) => hasCompleted(code) || hasPlanned(code)),
          missingCourses: ["MATH& 151", "MATH& 152"].filter((code) => !hasCompleted(code) && !hasPlanned(code)), confidence: schoolId === "uw" ? "high" : "medium",
          citationIds: [schoolId === "uw" ? "uw-equivalency" : schoolId === "berkeley" ? "berkeley-data" : "ucla-transfer"],
        },
        {
          id: `${majorId}-programming`, schoolId, majorId, category: "Major prerequisite", title: "Programming sequence",
          state: programmingUncertain ? "uncertain" : stateFor(["CS 141", "CS 210"]), completedCredits: (hasCompleted("CS 141") ? 5 : hasPlanned("CS 141") ? 2.5 : 0) + (hasCompleted("CS 210") ? 5 : hasPlanned("CS 210") ? 2.5 : 0), requiredCredits: 10,
          matchedCourses: ["CS 141", "CS 210"].filter((code) => hasCompleted(code) || hasPlanned(code)), missingCourses: hasCompleted("CS 210") || hasPlanned("CS 210") ? [] : ["Data Structures"], confidence: programmingUncertain ? "medium" : "high",
          citationIds: schoolId === "uw" ? ["uw-equivalency", "uw-info"] : [schoolId === "berkeley" ? "berkeley-data" : "ucla-transfer"],
        },
        {
          id: `${majorId}-statistics`, schoolId, majorId, category: "Major prerequisite", title: "Statistics or probability",
          state: stateFor(["MATH& 146"]), completedCredits: hasCompleted("MATH& 146") ? 5 : hasPlanned("MATH& 146") ? 2.5 : 0, requiredCredits: 5, matchedCourses: hasCompleted("MATH& 146") || hasPlanned("MATH& 146") ? ["MATH& 146"] : [], missingCourses: hasCompleted("MATH& 146") || hasPlanned("MATH& 146") ? [] : ["Introductory Statistics"], confidence: "medium",
          citationIds: [schoolId === "uw" ? "uw-info" : schoolId === "berkeley" ? "berkeley-data" : "ucla-transfer"],
        },
      ] satisfies RequirementResult[];
    });
  }
}

// MOCK IMPLEMENTATION: production graph should be constructed from term-aware prerequisite policies.
export class MockPrerequisiteGraphService implements PrerequisiteGraphService {
  async build(input: AcademicAnalysisInput): Promise<PrerequisiteChain[]> {
    const completedCodes = new Set(input.transcript.courses.filter(isPassing).map((course) => course.code.toUpperCase()));
    const inProgressCodes = new Set([
      ...input.transcript.courses.filter((course) => course.status === "in-progress").map((course) => course.code.toUpperCase()),
      ...input.scenario.plannedCourses.map((course) => course.course.toUpperCase()),
    ]);
    const stateFor = (code: string): RequirementState => completedCodes.has(code) ? "complete" : inProgressCodes.has(code) ? "in-progress" : "missing";
    const plannedTerm = (code: string, fallback: string) => input.scenario.plannedCourses.find((course) => course.course.toUpperCase() === code)?.termLabel ?? fallback;
    return targetPairs(input)
      .filter(({ majorId }) => /computer|informatics|data|statistics/.test(majorId))
      .map(({ schoolId, majorId }) => ({
        id: `${majorId}-data-structures-chain`,
        schoolId,
        majorId,
        targetCourse: "Data Structures",
        bottleneck: "Completing the second programming course unlocks Data Structures in the following term.",
        confidence: schoolId === "uw" ? "medium" : "low",
        citationIds: [schoolId === "uw" ? "uw-info" : schoolId === "berkeley" ? "berkeley-data" : "ucla-transfer"],
        steps: [
          { course: "CS 141", title: "Computer Science I", state: stateFor("CS 141"), earliestTerm: completedCodes.has("CS 141") ? "Completed" : plannedTerm("CS 141", "Next available term"), minimumGrade: "2.0 / C" },
          { course: "CS 142", title: "Computer Science II", state: stateFor("CS 142"), earliestTerm: plannedTerm("CS 142", "Winter 2026"), minimumGrade: "2.0 / C" },
          { course: "CS 210", title: "Data Structures", state: stateFor("CS 210"), earliestTerm: plannedTerm("CS 210", "After CS 142"), minimumGrade: "2.0 / C" },
        ],
      }));
  }
}

// MOCK IMPLEMENTATION: recommendations are deterministic examples driven by the selected scenario.
export class MockCourseRecommendationEngine implements CourseRecommendationEngine {
  async recommend(input: AcademicAnalysisInput, requirements: RequirementResult[]): Promise<CourseRecommendation[]> {
    void requirements;
    const pairs = targetPairs(input);
    const selectedSchoolNames = input.targets.map((target) => getSchool(target.schoolId)?.shortName ?? target.schoolId);
    const selectedMajorNames = pairs.map((pair) => getMajor(pair.majorId)?.name ?? pair.majorId);
    const citationIds = input.targets.flatMap((target) => getSchool(target.schoolId)?.citations.map((citation) => citation.id) ?? []);
    const optionCount = Math.max(pairs.length, 1);
    const templates: CourseRecommendation[] = [
      {
        id: "rec-stats", course: "MATH& 146", title: "Introduction to Statistics", credits: 5, priority: 1,
        optionCount, acceptedBy: selectedSchoolNames, supportsMajors: selectedMajorNames, satisfies: ["Statistics prerequisite", "Quantitative reasoning"],
        unlocks: ["Data methods", "Probability"], whyNow: "It fills the most common missing prerequisite across the selected programs.",
        impactIfSkipped: "At least two selected program paths remain incomplete for the next application cycle.", confidence: "medium", citationIds,
      },
      {
        id: "rec-data-structures", course: "CS 210", title: "Fundamentals of Data Structures", credits: 5, priority: 2,
        optionCount: Math.max(optionCount - 1, 1), acceptedBy: selectedSchoolNames, supportsMajors: selectedMajorNames.filter((major) => /Data|Computer|Informatics|Statistics/.test(major)),
        satisfies: ["Programming sequence"], unlocks: ["Algorithms", "Upper-division programming"],
        whyNow: "It completes the visible programming bottleneck immediately after CS 142.",
        impactIfSkipped: "The earliest major-ready term moves back by one quarter in this sample scenario.", confidence: "medium", citationIds,
      },
      {
        id: "rec-linear-algebra", course: "MATH& 208", title: "Linear Algebra", credits: 5, priority: 3,
        optionCount: Math.max(optionCount - 1, 1), acceptedBy: selectedSchoolNames, supportsMajors: selectedMajorNames,
        satisfies: ["Quantitative elective", "Major preparation"], unlocks: ["Machine learning", "Advanced statistics"],
        whyNow: "It preserves both computing and data-focused options while building on the completed calculus sequence.",
        impactIfSkipped: "It may need to be taken after transfer, reducing first-term flexibility.", confidence: "medium", citationIds,
      },
      {
        id: "rec-english", course: "ENGL& 102", title: "Composition II", credits: 5, priority: 4,
        optionCount, acceptedBy: selectedSchoolNames, supportsMajors: selectedMajorNames, satisfies: ["Writing", "General education"], unlocks: ["Writing-intensive coursework"],
        whyNow: "A second composition course is a broadly useful, option-preserving general education choice.",
        impactIfSkipped: "A writing requirement may remain outstanding after transfer.", confidence: "high", citationIds,
      },
      {
        id: "rec-natural-science", course: "PHYS& 114", title: "General Physics I", credits: 5, priority: 5,
        optionCount: Math.max(optionCount - 2, 1), acceptedBy: selectedSchoolNames, supportsMajors: selectedMajorNames,
        satisfies: ["Natural science", "Lab science"], unlocks: ["Physics II"],
        whyNow: "It adds lab science breadth without closing any selected path in the sample model.",
        impactIfSkipped: "Natural science may remain a post-transfer general education requirement.", confidence: "medium", citationIds,
      },
    ];
    const limit = input.scenario.preferredCreditLoad <= 12 ? 3 : input.scenario.preferredCreditLoad <= 16 ? 4 : 5;
    return templates.slice(0, limit);
  }
}

function buildReadiness(input: AcademicAnalysisInput, requirements: RequirementResult[], credits: CreditSummary): ProgramReadiness[] {
  return targetPairs(input).map(({ schoolId, majorId }) => {
    const programRequirements = requirements.filter((requirement) => requirement.majorId === majorId);
    const complete = programRequirements.filter((requirement) => requirement.state === "complete").length;
    const inProgress = programRequirements.filter((requirement) => requirement.state === "in-progress").length;
    const uncertain = programRequirements.filter((requirement) => requirement.state === "uncertain").length;
    const school = getSchool(schoolId);
    const pathwayBoost = input.scenario.institutionType === "in-state-community-college" && schoolId === "uw" ? 5 : 0;
    const residencyBoost = input.scenario.residency === "in-state" && schoolId === "uw" ? 2 : 0;
    const projectedGpa = calculateProjectedGpa(input.transcript);
    const gpaMinimumMet = projectedGpa >= 3;
    const rawScore = (complete / Math.max(programRequirements.length, 1)) * 75 + inProgress * 6 + pathwayBoost + residencyBoost - uncertain * 2 + (gpaMinimumMet ? 2 : -8);
    const score = Math.round(clamp(rawScore, 24, 94));
    const creditMinimumMet = credits.estimatedTransferable >= (school?.minimumTransferCredits ?? 60);
    const status = !creditMinimumMet || !gpaMinimumMet ? "not-eligible" : uncertain > 1 ? "manual-confirmation" : score >= 80 ? "ready" : score >= 60 ? "nearly-ready" : "preparation-recommended";
    return {
      schoolId, majorId, score, status, completedPrerequisites: complete, totalPrerequisites: programRequirements.length,
      creditMinimumMet, gpaMinimumMet, earliestApplicationTerm: creditMinimumMet ? input.scenario.targetTransferTerm : "After one additional term",
      unresolvedQuestions: uncertain,
    };
  });
}

const academicTerms = ["Winter", "Spring", "Summer", "Fall"] as const;

function parseTerm(value: string) {
  const [season = "Fall", yearText = "2027"] = value.split(" ");
  return { season: academicTerms.includes(season as typeof academicTerms[number]) ? season as typeof academicTerms[number] : "Fall", year: Number(yearText) || 2027 };
}

function nextAcademicTerm(value: string, attendSummer: boolean) {
  const { season, year } = parseTerm(value);
  const available: readonly string[] = attendSummer ? academicTerms : academicTerms.filter((term) => term !== "Summer");
  const currentIndex = available.indexOf(season);
  const nextIndex = currentIndex >= 0 ? (currentIndex + 1) % available.length : 0;
  const nextSeason = available[nextIndex];
  const nextYear = nextSeason === "Winter" && season !== "Winter" ? year + 1 : year;
  return `${nextSeason} ${nextYear}`;
}

function estimateGraduationTerm(startTerm: string, termsRemaining: number, attendSummer: boolean) {
  let term = startTerm;
  for (let index = 1; index < Math.max(termsRemaining, 1); index += 1) term = nextAcademicTerm(term, attendSummer);
  return term;
}

function termOrdinal(value: string) {
  const { season, year } = parseTerm(value);
  return year * 4 + academicTerms.indexOf(season);
}

function buildSimulationSummary(
  input: AcademicAnalysisInput,
  requirements: RequirementResult[],
  readiness: ProgramReadiness[],
  credits: CreditSummary,
): SimulationSummary {
  const generalEducation = requirements.filter((requirement) => requirement.category === "General education");
  const generalEducationRequired = generalEducation.reduce((sum, requirement) => sum + requirement.requiredCredits, 0);
  const generalEducationCompleted = generalEducation.reduce((sum, requirement) => sum + requirement.completedCredits, 0);
  const plannedCredits = input.scenario.plannedCourses.reduce((sum, course) => sum + course.credits, 0);
  const estimatedRemainingCredits = Math.max(0, Math.ceil(180 - credits.degreeApplicable));
  const termsRemaining = Math.ceil(estimatedRemainingCredits / Math.max(input.scenario.preferredCreditLoad, 1));
  const estimatedGraduationTerm = estimateGraduationTerm(input.scenario.targetTransferTerm, termsRemaining, input.scenario.attendSummer);
  const termLoads = input.scenario.plannedCourses.reduce<Record<string, number>>((totals, course) => ({ ...totals, [course.termId]: (totals[course.termId] ?? 0) + course.credits }), {});
  const missingPrerequisites = new Set(requirements
    .filter((requirement) => requirement.category === "Major prerequisite" && (requirement.state === "missing" || requirement.state === "uncertain"))
    .map((requirement) => `${requirement.schoolId}:${requirement.title}`));
  const openOptionIds = readiness.filter((program) => program.status !== "not-eligible").map((program) => program.majorId);

  return {
    totalPrograms: readiness.length,
    transferEligiblePrograms: readiness.filter((program) => program.creditMinimumMet).length,
    majorEligiblePrograms: readiness.filter((program) => program.status === "ready" || program.status === "nearly-ready").length,
    missingPrerequisiteCount: missingPrerequisites.size,
    generalEducationPercent: generalEducationRequired ? Math.round((generalEducationCompleted / generalEducationRequired) * 100) : 0,
    plannedCredits,
    projectedTransferableCredits: credits.estimatedTransferable,
    estimatedRemainingCredits,
    estimatedGraduationTerm,
    graduationTarget: input.scenario.graduationTarget,
    onTrackForGraduationTarget: termOrdinal(estimatedGraduationTerm) <= termOrdinal(input.scenario.graduationTarget),
    termsRemaining,
    openOptionIds,
    projectedGpa: calculateProjectedGpa(input.transcript),
    overloadedTermIds: Object.entries(termLoads).filter(([, total]) => total > input.scenario.preferredCreditLoad).map(([termId]) => termId),
  };
}

function buildAlerts(input: AcademicAnalysisInput, credits: CreditSummary, equivalencies: CourseEquivalency[]): AnalysisAlert[] {
  const alerts: AnalysisAlert[] = [
    {
      id: "alert-demo-data", severity: "info", title: "Sample policy analysis",
      message: "All policy conclusions and citations in this prototype are realistic demo data and have not been verified for enrollment decisions.",
      confidence: "low", office: "Admissions", canDraftEmail: false, citationIds: [],
    },
  ];
  if (input.scenario.useExamCredit) {
    alerts.push({
      id: "alert-ap-credit", severity: "warning", title: "AP Calculus use varies by program",
      message: "The sample model awards general credit, but does not confirm that every selected department accepts it for major admission.",
      confidence: "medium", office: "Department advisor", canDraftEmail: true,
      citationIds: input.targets.flatMap((target) => getSchool(target.schoolId)?.citations.slice(0, 1).map((citation) => citation.id) ?? []),
    });
  }
  const uncertainProgramming = equivalencies.find((equivalency) => equivalency.sourceCourse === "CS 141" && equivalency.confirmationRecommended);
  if (uncertainProgramming) {
    alerts.push({
      id: "alert-cs-equivalency", severity: "critical", title: "Programming equivalency needs confirmation",
      message: `${uncertainProgramming.sourceCourse} has no stored destination-course mapping, so its transfer and prerequisite use require manual confirmation.`,
      confidence: "medium", office: "Department advisor", canDraftEmail: true, citationIds: uncertainProgramming.citationIds,
    });
  }
  const minimums = input.targets.map((target) => getSchool(target.schoolId)?.minimumTransferCredits ?? 60);
  if (minimums.some((minimum) => credits.estimatedTransferable < minimum)) {
    alerts.push({
      id: "alert-credit-minimum", severity: "warning", title: "One target needs more transferable credits",
      message: "The current estimate is below at least one sample transfer-credit minimum. In-progress credit may close the gap.",
      confidence: "medium", office: "Admissions", canDraftEmail: true,
      citationIds: input.targets.flatMap((target) => getSchool(target.schoolId)?.citations.slice(0, 1).map((citation) => citation.id) ?? []),
    });
  }
  return alerts;
}

// MOCK IMPLEMENTATION: orchestrates all interfaces so the UI never owns analysis rules.
export class MockScenarioSimulator implements ScenarioSimulator {
  constructor(
    private readonly policyRetrieval: PolicyRetrievalService,
    private readonly equivalencyAnalyzer: EquivalencyAnalyzer,
    private readonly verificationEvaluator: VerificationEvaluator,
    private readonly requirementEvaluator: RequirementEvaluator,
    private readonly prerequisiteGraph: PrerequisiteGraphService,
    private readonly recommendationEngine: CourseRecommendationEngine,
  ) {}

  async simulate(input: AcademicAnalysisInput): Promise<AnalysisResult> {
    const [, equivalencies, prerequisiteChains] = await Promise.all([
      this.policyRetrieval.retrieve(input),
      this.equivalencyAnalyzer.analyze(input),
      this.prerequisiteGraph.build(input),
    ]);
    const requirements = await this.requirementEvaluator.evaluate(input, equivalencies);
    const verifications = await this.verificationEvaluator.evaluate(input, equivalencies);
    const recommendations = await this.recommendationEngine.recommend(input, requirements);
    const creditSummary = calculateCreditSummary(input);
    const readiness = buildReadiness(input, requirements, creditSummary);
    return {
      generatedAt: new Date().toISOString(),
      dataMode: "sample",
      scenarioLabel: `${input.scenario.currentInstitution} · ${input.scenario.residency === "in-state" ? "In-state" : input.scenario.residency === "out-of-state" ? "Out-of-state" : "International"} · ${input.scenario.preferredCreditLoad} credits max · ${input.scenario.useExamCredit ? "AP/IB on" : "AP/IB off"}`,
      simulationSummary: buildSimulationSummary(input, requirements, readiness, creditSummary),
      creditSummary,
      readiness,
      requirements,
      equivalencies,
      prerequisiteChains,
      recommendations,
      alerts: buildAlerts(input, creditSummary, equivalencies),
      verifications,
      citations: sampleCitations.filter((citation) => input.targets.some((target) => citation.id.startsWith(`${target.schoolId}-`))),
    };
  }
}

// MOCK IMPLEMENTATION: replace with a grounded GPT-5.6 response using stored context and structured citations.
export class MockAdvisorChatService implements AdvisorChatService {
  async answer(input: AdvisorInput): Promise<AdvisorAnswer> {
    const question = input.question.toLowerCase();
    const credits = input.analysis.creditSummary;
    let content: string;
    let citationIds: string[];
    if (question.includes("ap") || question.includes("ib")) {
      content = `Your AP Calculus BC score adds ${credits.examCredits} estimated credits in this scenario. The important caveat is that university credit and major-prerequisite credit are different decisions. The sample analysis cannot confirm department-level acceptance for every selected major, so verify before using the score to skip calculus.`;
      citationIds = input.analysis.citations.slice(0, 2).map((citation) => citation.id);
    } else if (question.includes("next") || question.includes("course") || question.includes("take")) {
      const top = input.analysis.recommendations[0];
      content = top
        ? `${top.course} — ${top.title} is the strongest option-preserving next course in this scenario. It supports ${top.optionCount} selected program options and addresses ${top.satisfies.join(" and ")}. ${top.whyNow}`
        : "Add at least one target major so I can compare option-preserving courses.";
      citationIds = top?.citationIds.slice(0, 2) ?? [];
    } else if (question.includes("graduat") || question.includes("remaining") || question.includes("timeline")) {
      const summary = input.analysis.simulationSummary;
      content = `This scenario estimates ${summary.estimatedRemainingCredits} credits and about ${summary.termsRemaining} terms remaining, with an estimated graduation term of ${summary.estimatedGraduationTerm}. That is ${summary.onTrackForGraduationTarget ? "on track for" : "later than"} the selected ${summary.graduationTarget} target. The estimate assumes a maximum of ${input.scenario.preferredCreditLoad} credits per term${input.scenario.attendSummer ? " and includes summer study" : " without summer study"}.`;
      citationIds = input.analysis.citations.slice(0, 2).map((citation) => citation.id);
    } else if (question.includes("transfer") || question.includes("eligible") || question.includes("apply")) {
      const readyCount = input.analysis.readiness.filter((item) => item.creditMinimumMet).length;
      content = `You currently have ${credits.earned} earned college credits and about ${credits.estimatedTransferable} estimated transferable credits in the sample model. ${readyCount} of ${input.analysis.readiness.length} selected programs meet their sample credit minimum now; in-progress work may move the others into range. This is readiness guidance, not an admission prediction.`;
      citationIds = input.analysis.citations.slice(0, 2).map((citation) => citation.id);
    } else {
      content = `Your plan is strongest on writing and the calculus sequence. The biggest shared bottlenecks are statistics, Data Structures, and ${input.analysis.alerts.filter((alert) => alert.canDraftEmail).length} unresolved policy question(s). I would prioritize the first recommended course and confirm the programming equivalency before registration.`;
      citationIds = input.analysis.citations.slice(0, 2).map((citation) => citation.id);
    }
    return {
      message: {
        id: `advisor-${Date.now()}`,
        role: "assistant",
        content: `${content} All cited policy details are sample, unverified demo data.`,
        createdAt: new Date().toISOString(),
        confidence: "medium",
        citationIds,
      },
      assumptions: [
        `Maximum load remains ${input.scenario.preferredCreditLoad} credits per term.`,
        `Current school is ${input.scenario.currentInstitution}.`,
        `The transcript contains ${input.transcript.courses.length} reviewed course records.`,
        "No selected program policy has been independently verified in this demo.",
      ],
      suggestedQuestions: ["What should I take next term?", "Does my AP Calculus credit count?", "Am I ready to apply?"],
    };
  }
}

// MOCK IMPLEMENTATION: email text should later include the exact retrieved policy gap and destination address.
export class MockUncertaintyEscalationHandler implements UncertaintyEscalationHandler {
  async draftEmail(item: VerificationItem, input: AcademicAnalysisInput): Promise<DraftEmail> {
    const selectedPrograms = targetPairs(input)
      .map(({ schoolId, majorId }) => `${getSchool(schoolId)?.shortName ?? schoolId} ${getMajor(majorId)?.name ?? majorId}`)
      .join(", ");
    const sourceSummary = item.sourceChecks.map((check) => {
      const citation = sampleCitations.find((candidate) => candidate.id === check.citationId);
      return `- ${citation?.title ?? check.citationId}: ${check.note}`;
    }).join("\n");
    return {
      toOffice: item.office,
      subject: `Transfer evaluation request: ${item.sourceCourse} from ${item.sourceInstitution}`,
      body: `Hello,\n\nI am requesting guidance about ${item.sourceCourse}, taken at ${item.sourceInstitution} in ${item.sourceTerm}. I am planning for ${selectedPrograms || getSchool(item.destinationSchoolId)?.shortName || item.destinationSchoolId} and targeting ${input.scenario.targetTransferTerm}.\n\nMy exact question is:\n${item.question}\n\nThe saved sources I checked were:\n${sourceSummary}\n\nThe planning tool did not assign an equivalency that was not explicitly present in those records. Could your office confirm the result and let me know whether you need a syllabus or course description for manual evaluation?\n\nThank you for your help.`,
      context: {
        course: item.sourceCourse,
        institution: item.sourceInstitution,
        term: item.sourceTerm,
        question: item.question,
      },
    };
  }
}
