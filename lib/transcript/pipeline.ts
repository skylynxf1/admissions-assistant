import "server-only";
import type { TranscriptPdfParser } from "@/lib/transcript/parsers/interface";
import type { TranscriptStructuredExtractor } from "@/lib/transcript/extractors/interface";
import type { TranscriptPipelineResult } from "@/lib/transcript/types";
import { DoclingParserClient } from "@/lib/transcript/parsers/docling-client";
import { MarkerParserClient } from "@/lib/transcript/parsers/marker-client";
import { OpenAITranscriptExtractor } from "@/lib/transcript/extractors/openai-transcript-extractor";
import { normalizeTranscriptExtraction } from "@/lib/transcript/normalizer";
import { validateTranscriptExtraction } from "@/lib/transcript/validator";

export interface TranscriptPipelineDependencies {
  primaryParser?: TranscriptPdfParser;
  fallbackParser?: TranscriptPdfParser;
  extractor?: TranscriptStructuredExtractor;
}

export async function runTranscriptPipeline(file: File, dependencies: TranscriptPipelineDependencies = {}): Promise<TranscriptPipelineResult> {
  const primary = dependencies.primaryParser ?? new DoclingParserClient();
  const fallback = dependencies.fallbackParser ?? (process.env.TRANSCRIPT_MARKER_FALLBACK === "true" ? new MarkerParserClient() : undefined);
  let parsedDocument;
  try {
    parsedDocument = await primary.parse(file);
  } catch (primaryError) {
    if (!fallback) throw primaryError;
    parsedDocument = await fallback.parse(file);
  }
  if (!parsedDocument.pageCount || !parsedDocument.markdown.trim()) throw new Error("The parser returned an empty transcript.");

  const extractor = dependencies.extractor ?? new OpenAITranscriptExtractor();
  const rawExtraction = await extractor.extract(parsedDocument);
  const normalizedExtraction = normalizeTranscriptExtraction(rawExtraction);
  const validatedTranscript = validateTranscriptExtraction(normalizedExtraction, parsedDocument.pageCount);
  return {
    documentId: crypto.randomUUID(),
    fileName: file.name,
    status: validatedTranscript.requiresReview ? "needs_review" : "completed",
    parseRunId: crypto.randomUUID(),
    parsedDocument,
    validatedTranscript,
    mode: "supabase",
  };
}
