import "server-only";
import { createHash } from "node:crypto";

export const MAX_TRANSCRIPT_PDF_BYTES = 15 * 1024 * 1024;

export type PdfValidationResult =
  | { ok: true; bytes: Uint8Array; sha256: string }
  | { ok: false; code: "missing_file" | "invalid_type" | "too_large" | "empty_pdf" | "protected_pdf" | "corrupt_pdf"; message: string };

export async function validateTranscriptPdf(file: File | null): Promise<PdfValidationResult> {
  if (!file) return { ok: false, code: "missing_file", message: "Choose a transcript PDF to continue." };
  if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
    return { ok: false, code: "invalid_type", message: "Transcript uploads must be PDF files." };
  }
  if (file.size > MAX_TRANSCRIPT_PDF_BYTES) {
    return { ok: false, code: "too_large", message: "The PDF is larger than the 15 MB upload limit." };
  }
  if (file.size === 0) return { ok: false, code: "empty_pdf", message: "The PDF is empty." };

  const bytes = new Uint8Array(await file.arrayBuffer());
  const head = new TextDecoder("latin1").decode(bytes.slice(0, Math.min(bytes.length, 2048)));
  const body = new TextDecoder("latin1").decode(bytes);
  if (!head.includes("%PDF-")) return { ok: false, code: "corrupt_pdf", message: "The file does not have a valid PDF header." };
  if (/\/Encrypt\b/.test(body)) return { ok: false, code: "protected_pdf", message: "Password-protected PDFs are not supported. Export an unlocked copy and try again." };
  if (!/%%EOF\s*$/.test(body.trim())) return { ok: false, code: "corrupt_pdf", message: "The PDF appears incomplete or corrupted." };
  return { ok: true, bytes, sha256: createHash("sha256").update(bytes).digest("hex") };
}
