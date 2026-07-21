import type { AcademicPlanningServices } from "@/lib/services/interfaces";
import {
  MockAcademicRecordNormalizer,
  MockAdvisorChatService,
  MockCourseRecommendationEngine,
  MockEquivalencyAnalyzer,
  MockPolicyRetrievalService,
  MockPrerequisiteGraphService,
  MockRequirementEvaluator,
  MockScenarioSimulator,
  MockTranscriptParser,
  MockTransferOutcomeService,
  MockUncertaintyEscalationHandler,
  MockVerificationEvaluator,
} from "@/lib/services/mock";
import { RealTransferOutcomeService } from "@/lib/services/real/transfer-outcomes";

// Per-service real/mock selection: only the flags listed here exist, and each gates
// exactly one service. There is no global "use real services" switch — every other
// service in the registry below stays mock regardless of these flags.
const useRealTransferOutcomes = process.env.NEXT_PUBLIC_USE_REAL_TRANSFER_OUTCOMES === "true";

const policyRetrieval = new MockPolicyRetrievalService();
const equivalencyAnalyzer = new MockEquivalencyAnalyzer();
const verificationEvaluator = new MockVerificationEvaluator();
const requirementEvaluator = new MockRequirementEvaluator();
const prerequisiteGraph = new MockPrerequisiteGraphService();
const recommendationEngine = new MockCourseRecommendationEngine();

export const academicPlanningServices: AcademicPlanningServices = {
  transcriptParser: new MockTranscriptParser(),
  normalizer: new MockAcademicRecordNormalizer(),
  policyRetrieval,
  equivalencyAnalyzer,
  verificationEvaluator,
  requirementEvaluator,
  prerequisiteGraph,
  recommendationEngine,
  scenarioSimulator: new MockScenarioSimulator(
    policyRetrieval,
    equivalencyAnalyzer,
    verificationEvaluator,
    requirementEvaluator,
    prerequisiteGraph,
    recommendationEngine,
  ),
  advisorChat: new MockAdvisorChatService(),
  uncertaintyHandler: new MockUncertaintyEscalationHandler(),
  transferOutcomes: useRealTransferOutcomes ? new RealTransferOutcomeService() : new MockTransferOutcomeService(),
};
