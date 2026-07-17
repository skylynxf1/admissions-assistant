import "server-only";
import type { ParsedTranscriptDocument } from "@/lib/transcript/types";
import type { TranscriptPdfParser } from "@/lib/transcript/parsers/interface";
import { TranscriptParserError } from "@/lib/transcript/parsers/interface";

// Optional fast path for text-native PDFs. It shares the same normalized parser contract.
export class PyMuPdfParserClient implements TranscriptPdfParser {
  readonly name = "pymupdf" as const;
  constructor(private readonly baseUrl = process.env.DOCLING_SERVICE_URL) {}
  async parse(file: File): Promise<ParsedTranscriptDocument> {
    if (!this.baseUrl) throw new TranscriptParserError("Transcript parser service is not configured.", "parser_unavailable");
    const form = new FormData();
    form.set("file", file, file.name);
    const response = await fetch(`${this.baseUrl.replace(/\/$/, "")}/parse?parser=pymupdf`, { method: "POST", body: form, signal: AbortSignal.timeout(60_000) });
    if (!response.ok) throw new TranscriptParserError("PyMuPDF fast path failed.", "parser_failed");
    return response.json() as Promise<ParsedTranscriptDocument>;
  }
}
