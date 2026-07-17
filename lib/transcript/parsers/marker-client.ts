import "server-only";
import type { ParsedTranscriptDocument } from "@/lib/transcript/types";
import type { TranscriptPdfParser } from "@/lib/transcript/parsers/interface";
import { TranscriptParserError } from "@/lib/transcript/parsers/interface";

// Optional fallback adapter. The Python service returns 501 until Marker is installed and enabled.
export class MarkerParserClient implements TranscriptPdfParser {
  readonly name = "marker" as const;
  constructor(private readonly baseUrl = process.env.DOCLING_SERVICE_URL) {}
  async parse(file: File): Promise<ParsedTranscriptDocument> {
    if (!this.baseUrl) throw new TranscriptParserError("Transcript parser service is not configured.", "parser_unavailable");
    const form = new FormData();
    form.set("file", file, file.name);
    const response = await fetch(`${this.baseUrl.replace(/\/$/, "")}/parse?parser=marker`, { method: "POST", body: form, signal: AbortSignal.timeout(120_000) });
    if (!response.ok) throw new TranscriptParserError("Marker fallback is unavailable.", "parser_unavailable");
    return response.json() as Promise<ParsedTranscriptDocument>;
  }
}
