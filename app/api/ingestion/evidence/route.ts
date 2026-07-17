import { timingSafeEqual } from "node:crypto";
import { NextResponse } from "next/server";
import { isEvidenceIngestRequest } from "@/lib/backend/types";
import { SupabaseEvidenceRepository } from "@/lib/backend/repositories/evidence-repository";
import { getSupabaseAdminClient } from "@/lib/supabase/server";

function secretMatches(received: string | null, expected: string | undefined) {
  if (!received || !expected) return false;
  const left = Buffer.from(received);
  const right = Buffer.from(expected);
  return left.length === right.length && timingSafeEqual(left, right);
}

export async function POST(request: Request) {
  if (!secretMatches(request.headers.get("x-ingestion-secret"), process.env.INGESTION_API_KEY)) {
    return NextResponse.json({ error: "Trusted ingestion credentials are required." }, { status: 401 });
  }
  const adminClient = getSupabaseAdminClient();
  if (!adminClient) return NextResponse.json({ error: "Supabase admin access is not configured." }, { status: 503 });
  try {
    const body: unknown = await request.json();
    if (!isEvidenceIngestRequest(body)) return NextResponse.json({ error: "Invalid evidence payload" }, { status: 422 });
    const repository = new SupabaseEvidenceRepository(adminClient);
    return NextResponse.json({ data: await repository.ingest(body), meta: { mode: "supabase", reviewStatus: "pending" } }, { status: 201 });
  } catch (error) {
    return NextResponse.json({ error: "Evidence ingestion failed", detail: error instanceof Error ? error.message : "Unknown error" }, { status: 500 });
  }
}
