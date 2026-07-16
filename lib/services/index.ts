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
  MockUncertaintyEscalationHandler,
} from "@/lib/services/mock";

const policyRetrieval = new MockPolicyRetrievalService();
const equivalencyAnalyzer = new MockEquivalencyAnalyzer();
const requirementEvaluator = new MockRequirementEvaluator();
const prerequisiteGraph = new MockPrerequisiteGraphService();
const recommendationEngine = new MockCourseRecommendationEngine();

export const academicPlanningServices: AcademicPlanningServices = {
  transcriptParser: new MockTranscriptParser(),
  normalizer: new MockAcademicRecordNormalizer(),
  policyRetrieval,
  equivalencyAnalyzer,
  requirementEvaluator,
  prerequisiteGraph,
  recommendationEngine,
  scenarioSimulator: new MockScenarioSimulator(
    policyRetrieval,
    equivalencyAnalyzer,
    requirementEvaluator,
    prerequisiteGraph,
    recommendationEngine,
  ),
  advisorChat: new MockAdvisorChatService(),
  uncertaintyHandler: new MockUncertaintyEscalationHandler(),
};
