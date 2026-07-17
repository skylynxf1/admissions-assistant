import type { AcademicAnalysisInput, AnalysisResult, TranscriptData } from "@/lib/types";
import type { ConfidenceLevel, Json, ReviewStatus, SourceType } from "@/lib/supabase/database.types";

export interface SaveTranscriptRequest {
  transcript: TranscriptData;
  profile: AcademicAnalysisInput["profile"];
}

export interface SaveScenarioRequest {
  clientId?: string;
  name?: string;
  planningMode?: string;
  prioritySchoolId?: string;
  input: AcademicAnalysisInput;
  analysis?: AnalysisResult | null;
}

export interface PersistedTranscript {
  id: string;
  courseCount: number;
  examScoreCount: number;
}

export interface PersistedScenario {
  id: string;
  resultId: string | null;
  updatedAt: string;
}

export interface EvidenceClaimInput {
  claimKey: string;
  claimType: string;
  exactQuote: string;
  locator?: Json;
  tableHeaders?: Json | null;
  tableRow?: Json | null;
  footnotes?: string[];
  normalizedValue?: Json | null;
  effectiveFrom?: string | null;
  effectiveTo?: string | null;
  confidence: ConfidenceLevel;
  reviewStatus?: ReviewStatus;
}

export interface EvidenceIngestRequest {
  institutionId: string;
  originalUrl: string;
  canonicalUrl: string;
  pageTitle?: string | null;
  sourceType: SourceType;
  official: boolean;
  retrievedAt: string;
  contentHash: string;
  mimeType?: string | null;
  storageBucket?: string | null;
  storagePath?: string | null;
  httpStatus?: number | null;
  catalogYear?: string | null;
  effectiveTerm?: string | null;
  rawText?: string | null;
  responseMetadata?: Json;
  parserRunId?: string | null;
  evidence: EvidenceClaimInput[];
}

export function isSaveScenarioRequest(value: unknown): value is SaveScenarioRequest {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<SaveScenarioRequest>;
  return Boolean(
    candidate.input?.profile
    && candidate.input?.transcript
    && candidate.input?.scenario
    && Array.isArray(candidate.input?.targets),
  );
}

export function isSaveTranscriptRequest(value: unknown): value is SaveTranscriptRequest {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<SaveTranscriptRequest>;
  return Boolean(candidate.profile && candidate.transcript && Array.isArray(candidate.transcript.courses));
}

export function isEvidenceIngestRequest(value: unknown): value is EvidenceIngestRequest {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<EvidenceIngestRequest>;
  return Boolean(
    candidate.institutionId
    && candidate.originalUrl
    && candidate.canonicalUrl
    && candidate.sourceType
    && candidate.retrievedAt
    && candidate.contentHash
    && Array.isArray(candidate.evidence)
    && candidate.evidence.every((item) => item.claimKey && item.claimType && item.exactQuote && item.confidence),
  );
}
