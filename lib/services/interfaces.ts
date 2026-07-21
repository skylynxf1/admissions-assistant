import type {
  AcademicAnalysisInput,
  AdvisorAnswer,
  AdvisorInput,
  AnalysisResult,
  CourseEquivalency,
  CourseRecord,
  CourseRecommendation,
  DraftEmail,
  PrerequisiteChain,
  RequirementResult,
  SchoolDefinition,
  TranscriptData,
  VerificationItem,
} from "@/lib/types";
import type { TransferOutcome } from "@/lib/transfer/types";

export interface TranscriptParser {
  parse(fileName?: string): Promise<TranscriptData>;
}

export interface AcademicRecordNormalizer {
  normalize(courses: CourseRecord[]): Promise<CourseRecord[]>;
}

export interface PolicyRetrievalService {
  retrieve(input: AcademicAnalysisInput): Promise<SchoolDefinition[]>;
}

export interface EquivalencyAnalyzer {
  analyze(input: AcademicAnalysisInput): Promise<CourseEquivalency[]>;
}

export interface VerificationEvaluator {
  evaluate(input: AcademicAnalysisInput, equivalencies: CourseEquivalency[]): Promise<VerificationItem[]>;
}

export interface RequirementEvaluator {
  evaluate(input: AcademicAnalysisInput, equivalencies: CourseEquivalency[]): Promise<RequirementResult[]>;
}

export interface PrerequisiteGraphService {
  build(input: AcademicAnalysisInput): Promise<PrerequisiteChain[]>;
}

export interface CourseRecommendationEngine {
  recommend(input: AcademicAnalysisInput, requirements: RequirementResult[]): Promise<CourseRecommendation[]>;
}

export interface ScenarioSimulator {
  simulate(input: AcademicAnalysisInput): Promise<AnalysisResult>;
}

export interface AdvisorChatService {
  answer(input: AdvisorInput): Promise<AdvisorAnswer>;
}

export interface UncertaintyEscalationHandler {
  draftEmail(item: VerificationItem, input: AcademicAnalysisInput): Promise<DraftEmail>;
}

// Real, cited UW transfer outcomes (Bellevue College -> UW Seattle). Unlike the other
// services above, this one has a working non-mock implementation — see
// lib/services/real/transfer-outcomes.ts. The adapter is a pure function of its input
// arguments; it must never read React context, localStorage, or other app state.
export interface TransferOutcomeRequestInput {
  pathwayKey: string;
  courses: { code: string; title?: string | null }[];
}

export interface TransferOutcomeServiceResult {
  available: boolean; // false when the backend is not reachable/configured
  unavailableReason?: string; // human-readable, shown in the UI
  outcomes: TransferOutcome[];
}

export interface TransferOutcomeService {
  resolve(input: TransferOutcomeRequestInput): Promise<TransferOutcomeServiceResult>;
}

export interface AcademicPlanningServices {
  transcriptParser: TranscriptParser;
  normalizer: AcademicRecordNormalizer;
  policyRetrieval: PolicyRetrievalService;
  equivalencyAnalyzer: EquivalencyAnalyzer;
  verificationEvaluator: VerificationEvaluator;
  requirementEvaluator: RequirementEvaluator;
  prerequisiteGraph: PrerequisiteGraphService;
  recommendationEngine: CourseRecommendationEngine;
  scenarioSimulator: ScenarioSimulator;
  advisorChat: AdvisorChatService;
  uncertaintyHandler: UncertaintyEscalationHandler;
  transferOutcomes: TransferOutcomeService;
}
