import type { ParsedTranscriptDocument, TranscriptExtraction } from "@/lib/transcript/types";

export interface TranscriptStructuredExtractor {
  extract(document: ParsedTranscriptDocument): Promise<TranscriptExtraction>;
}
