import "server-only";
import type { ParsedTranscriptDocument } from "@/lib/transcript/types";
import type { TranscriptPdfParser } from "@/lib/transcript/parsers/interface";
import { TranscriptParserError } from "@/lib/transcript/parsers/interface";

export class DoclingParserClient implements TranscriptPdfParser {
  readonly name = "docling" as const;

  constructor(private readonly baseUrl = process.env.DOCLING_SERVICE_URL) {}

  async parse(file: File): Promise<ParsedTranscriptDocument> {
    if (!this.baseUrl) throw new TranscriptParserError("DOCLING_SERVICE_URL is not configured.", "parser_unavailable");
    const form = new FormData();
    form.set("file", file, file.name);
    let response: Response;
    try {
      response = await fetch(`${this.baseUrl.replace(/\/$/, "")}/parse?parser=docling`, { method: "POST", body: form, signal: AbortSignal.timeout(120_000) });
    } catch (error) {
      throw new TranscriptParserError(error instanceof Error ? error.message : "Docling service is unavailable.", "parser_unavailable");
    }
    if (!response.ok) {
      const body = await response.json().catch(() => null) as {
        code?: TranscriptParserError["code"];
        detail?: string | { code?: TranscriptParserError["code"]; detail?: string };
      } | null;
      const nestedError = typeof body?.detail === "object" ? body.detail : null;
      const message = nestedError?.detail ?? (typeof body?.detail === "string" ? body.detail : undefined);
      const code = nestedError?.code ?? body?.code ?? "parser_failed";
      throw new TranscriptParserError(message || `Docling failed with status ${response.status}.`, code);
    }
    return response.json() as Promise<ParsedTranscriptDocument>;
  }
}
