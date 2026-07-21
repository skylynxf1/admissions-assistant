import { NextResponse } from "next/server";
import { fetchTransferOutcomes } from "@/lib/transfer/client";
import type { SourceCourseInput, TransferOutcomeRequest } from "@/lib/transfer/types";

function isSourceCourseInput(value: unknown): value is SourceCourseInput {
  if (typeof value !== "object" || value === null) return false;
  const candidate = value as Record<string, unknown>;
  if (typeof candidate.code !== "string" || candidate.code.trim() === "") return false;
  if (candidate.title !== undefined && candidate.title !== null && typeof candidate.title !== "string") return false;
  return true;
}

export async function POST(request: Request) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Request body must be valid JSON" }, { status: 400 });
  }

  const input = (body ?? {}) as Partial<TransferOutcomeRequest>;
  if (typeof input.pathway_key !== "string" || input.pathway_key.trim() === "") {
    return NextResponse.json({ error: "pathway_key is required and must be a non-empty string" }, { status: 400 });
  }
  if (!Array.isArray(input.courses) || !input.courses.every(isSourceCourseInput)) {
    return NextResponse.json({ error: "courses is required and must be an array of { code, title? }" }, { status: 400 });
  }

  try {
    const result = await fetchTransferOutcomes({ pathway_key: input.pathway_key, courses: input.courses });
    return NextResponse.json(result);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Transfer outcomes service is unavailable";
    return NextResponse.json({ error: message }, { status: 503 });
  }
}
