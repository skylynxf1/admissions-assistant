import type {
  AcademicAnalysisInput,
  AdvisorAnswer,
  AdvisorInput,
  AnalysisAlert,
  AnalysisResult,
  CourseEquivalency,
  CourseRecord,
  CourseRecommendation,
  DraftEmail,
  PrerequisiteChain,
  RequirementResult,
  SchoolDefinition,
  TranscriptData,
} from "@/lib/types";

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
  draftEmail(alert: AnalysisAlert, input: AcademicAnalysisInput): Promise<DraftEmail>;
}

export interface AcademicPlanningServices {
  transcriptParser: TranscriptParser;
  normalizer: AcademicRecordNormalizer;
  policyRetrieval: PolicyRetrievalService;
  equivalencyAnalyzer: EquivalencyAnalyzer;
  requirementEvaluator: RequirementEvaluator;
  prerequisiteGraph: PrerequisiteGraphService;
  recommendationEngine: CourseRecommendationEngine;
  scenarioSimulator: ScenarioSimulator;
  advisorChat: AdvisorChatService;
  uncertaintyHandler: UncertaintyEscalationHandler;
}
