import "server-only";
import { SupabaseTranscriptPipelineRepository } from "@/lib/backend/repositories/transcript-pipeline-repository";
import { runTranscriptPipeline } from "@/lib/transcript/pipeline";
import { DoclingParserClient } from "@/lib/transcript/parsers/docling-client";
import { MarkerParserClient } from "@/lib/transcript/parsers/marker-client";
import { PyMuPdfParserClient } from "@/lib/transcript/parsers/pymupdf-client";
import type { TranscriptParserName } from "@/lib/transcript/types";

export async function processStoredTranscript(
  repository: SupabaseTranscriptPipelineRepository,
  documentId: string,
  parserName: TranscriptParserName = "docling",
) {
  const download = await repository.download(documentId);
  if (!download) throw new Error("Transcript document was not found.");
  await repository.setStatus(documentId, "processing");
  const file = new File([download.blob], download.document.original_filename, { type: "application/pdf" });
  const parser = parserName === "pymupdf" ? new PyMuPdfParserClient() : parserName === "marker" ? new MarkerParserClient() : new DoclingParserClient();
  try {
    const pipeline = await runTranscriptPipeline(file, { primaryParser: parser });
    const document = await repository.persistPipelineResult(documentId, pipeline);
    return { document, pipeline: { ...pipeline, documentId, parseRunId: document.active_parse_run_id ?? pipeline.parseRunId } };
  } catch (error) {
    const failure = error instanceof Error ? error : new Error("Transcript processing failed.");
    await repository.persistFailure(documentId, parserName, failure);
    throw failure;
  }
}
