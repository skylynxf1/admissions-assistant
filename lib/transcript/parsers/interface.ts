import type { ParsedTranscriptDocument, TranscriptParserName } from "@/lib/transcript/types";

export interface TranscriptPdfParser {
  readonly name: TranscriptParserName;
  parse(file: File): Promise<ParsedTranscriptDocument>;
}

export class TranscriptParserError extends Error {
  constructor(
    message: string,
    readonly code: "protected_pdf" | "corrupt_pdf" | "empty_pdf" | "parser_unavailable" | "parser_failed",
  ) {
    super(message);
    this.name = "TranscriptParserError";
  }
}
