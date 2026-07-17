export type PlanningMode =
  | "first-year"
  | "transfer"
  | "current-degree"
  | "graduation"
  | "graduate-prereqs"
  | "mba"
  | "study-abroad";

export type ConfidenceLevel = "high" | "medium" | "low";
export type VerificationStatus =
  | "confirmed"
  | "likely"
  | "unclear"
  | "manual-evaluation"
  | "conflicting";
export type VerificationOffice =
  | "Admissions"
  | "Transfer credit office"
  | "Department advisor"
  | "Residency office";
export type CourseStatus = "completed" | "in-progress" | "planned";
export type RequirementState = "complete" | "in-progress" | "missing" | "uncertain";
export type EligibilityStatus =
  | "ready"
  | "nearly-ready"
  | "preparation-recommended"
  | "not-eligible"
  | "manual-confirmation";

export type InstitutionType =
  | "in-state-community-college"
  | "out-of-state-community-college"
  | "in-state-four-year"
  | "out-of-state-four-year"
  | "international";

export interface Citation {
  id: string;
  title: string;
  url: string;
  publisher: string;
  effectiveTerm: string;
  lastChecked: string;
  official: boolean;
  demoLabel: "sample-unverified";
}

export interface CourseRecord {
  id: string;
  institution: string;
  code: string;
  title: string;
  term: string;
  creditsAttempted: number;
  creditsEarned: number;
  grade: string;
  status: CourseStatus;
  confidence: ConfidenceLevel;
  repeat: boolean;
  transfer: boolean;
  notes?: string;
  sourcePage?: number;
  extractionConfidence?: number;
  rawText?: string;
  sourceDocumentId?: string;
  normalizedRecordId?: string;
  normalizedInstitutionId?: string;
  normalizedTermId?: string;
}

export interface ExamCredit {
  id: string;
  type: "AP" | "IB" | "CLEP" | "Other";
  subject: string;
  score: string;
  creditsAwarded: number;
  enabled: boolean;
  sourcePage?: number;
  extractionConfidence?: number;
  sourceDocumentId?: string;
  normalizedRecordId?: string;
}

export interface TranscriptData {
  id: string;
  fileName?: string;
  institutions: string[];
  courses: CourseRecord[];
  examCredits: ExamCredit[];
  cumulativeGpa: number;
  extractionStatus: "idle" | "extracting" | "complete" | "error";
  verificationStatus: "unreviewed" | "reviewing" | "confirmed";
}

export interface StudentProfile {
  firstName: string;
  currentInstitution: string;
  institutionType: InstitutionType;
  residency: "in-state" | "out-of-state" | "international";
  targetTransferTerm: string;
  preferredCreditLoad: number;
  currentlyEnrolled: boolean;
  hasExamCredit: boolean;
}

export interface MajorDefinition {
  id: string;
  name: string;
  college: string;
  admissionType: "open" | "capacity-constrained" | "direct" | "competitive";
}

export interface SchoolDefinition {
  id: string;
  name: string;
  shortName: string;
  location: string;
  color: string;
  minimumTransferCredits: number;
  preferredCreditRange: [number, number];
  maximumTransferCredits: number;
  majors: MajorDefinition[];
  citations: Citation[];
}

export interface TargetSchool {
  schoolId: string;
  majorIds: string[];
}

export interface PlannedCourse {
  id: string;
  course: string;
  title: string;
  credits: number;
  termId: string;
  termLabel: string;
  satisfies: string[];
  source: "recommended" | "custom";
}

export interface ScenarioSettings {
  currentInstitution: string;
  institutionType: InstitutionType;
  residency: StudentProfile["residency"];
  targetTransferTerm: string;
  preferredCreditLoad: number;
  graduationTarget: string;
  useExamCredit: boolean;
  attendSummer: boolean;
  plannedCourses: PlannedCourse[];
}

export interface CreditSummary {
  attempted: number;
  earned: number;
  estimatedTransferable: number;
  degreeApplicable: number;
  majorApplicable: number;
  inProgress: number;
  examCredits: number;
  electiveOnly: number;
}

export interface CourseEquivalency {
  id: string;
  sourceCourse: string;
  sourceInstitution: string;
  destinationSchoolId: string;
  destinationCourse: string;
  category: string;
  result: string;
  confidence: ConfidenceLevel;
  reasoning: string;
  confirmationRecommended: boolean;
  citationIds: string[];
}

export interface RequirementResult {
  id: string;
  schoolId: string;
  majorId: string;
  category: string;
  title: string;
  state: RequirementState;
  completedCredits: number;
  requiredCredits: number;
  matchedCourses: string[];
  missingCourses: string[];
  confidence: ConfidenceLevel;
  citationIds: string[];
}

export interface PrerequisiteStep {
  course: string;
  title: string;
  state: RequirementState;
  earliestTerm: string;
  minimumGrade?: string;
}

export interface PrerequisiteChain {
  id: string;
  schoolId: string;
  majorId: string;
  targetCourse: string;
  bottleneck: string;
  steps: PrerequisiteStep[];
  confidence: ConfidenceLevel;
  citationIds: string[];
}

export interface ProgramReadiness {
  schoolId: string;
  majorId: string;
  score: number;
  status: EligibilityStatus;
  completedPrerequisites: number;
  totalPrerequisites: number;
  creditMinimumMet: boolean;
  gpaMinimumMet: boolean;
  earliestApplicationTerm: string;
  unresolvedQuestions: number;
}

export interface CourseRecommendation {
  id: string;
  course: string;
  title: string;
  credits: number;
  priority: number;
  optionCount: number;
  acceptedBy: string[];
  supportsMajors: string[];
  satisfies: string[];
  unlocks: string[];
  whyNow: string;
  impactIfSkipped: string;
  confidence: ConfidenceLevel;
  citationIds: string[];
}

export interface AnalysisAlert {
  id: string;
  severity: "info" | "warning" | "critical";
  title: string;
  message: string;
  confidence: ConfidenceLevel;
  office: VerificationOffice;
  canDraftEmail: boolean;
  citationIds: string[];
}

export interface VerificationSourceCheck {
  citationId: string;
  outcome: "supports" | "does-not-address" | "conflicts";
  note: string;
}

export interface VerificationItem {
  id: string;
  status: VerificationStatus;
  title: string;
  conclusion: string;
  explanation: string;
  sourceCourse: string;
  sourceInstitution: string;
  sourceTerm: string;
  destinationSchoolId: string;
  /** Only populated when a saved source explicitly contains the destination mapping. */
  destinationCourse?: string;
  question: string;
  office: VerificationOffice;
  sourceChecks: VerificationSourceCheck[];
  canDraftEmail: boolean;
}

export interface AnalysisResult {
  generatedAt: string;
  dataMode: "sample";
  scenarioLabel: string;
  simulationSummary: SimulationSummary;
  creditSummary: CreditSummary;
  readiness: ProgramReadiness[];
  requirements: RequirementResult[];
  equivalencies: CourseEquivalency[];
  prerequisiteChains: PrerequisiteChain[];
  recommendations: CourseRecommendation[];
  alerts: AnalysisAlert[];
  verifications: VerificationItem[];
  citations: Citation[];
}

export interface SimulationSummary {
  totalPrograms: number;
  transferEligiblePrograms: number;
  majorEligiblePrograms: number;
  missingPrerequisiteCount: number;
  generalEducationPercent: number;
  plannedCredits: number;
  projectedTransferableCredits: number;
  estimatedRemainingCredits: number;
  estimatedGraduationTerm: string;
  graduationTarget: string;
  onTrackForGraduationTarget: boolean;
  termsRemaining: number;
  openOptionIds: string[];
  projectedGpa: number;
  overloadedTermIds: string[];
}

export interface PlanComparison {
  id: string;
  label: string;
  createdAt: string;
  prioritySchoolId: string;
  targets: TargetSchool[];
  scenario: ScenarioSettings;
  transcript: TranscriptData;
  summary: SimulationSummary;
}

export interface AdvisorMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  createdAt: string;
  confidence?: ConfidenceLevel;
  citationIds?: string[];
}

export interface AdvisorAnswer {
  message: AdvisorMessage;
  assumptions: string[];
  suggestedQuestions: string[];
}

export interface DraftEmail {
  toOffice: string;
  subject: string;
  body: string;
  context: {
    course: string;
    institution: string;
    term: string;
    question: string;
  };
}

export interface AcademicAnalysisInput {
  profile: StudentProfile;
  transcript: TranscriptData;
  targets: TargetSchool[];
  scenario: ScenarioSettings;
}

export interface AdvisorInput extends AcademicAnalysisInput {
  question: string;
  analysis: AnalysisResult;
  history: AdvisorMessage[];
}
