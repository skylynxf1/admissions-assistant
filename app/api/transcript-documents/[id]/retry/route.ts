import { NextResponse } from "next/server";
import { getBackendAuthContext } from "@/lib/backend/auth";
import { SupabaseTranscriptPipelineRepository } from "@/lib/backend/repositories/transcript-pipeline-repository";
import { processStoredTranscript } from "@/lib/transcript/process-document";
import type { TranscriptParserName } from "@/lib/transcript/types";

export const maxDuration = 180;
type Context = { params: Promise<{ id: string }> };

export async function POST(request: Request, context: Context) {
  const auth = await getBackendAuthContext(request);
  if (auth.status === "unconfigured") return NextResponse.json({ error: "Supabase is not configured." }, { status: 503 });
  if (auth.status === "unauthorized") return NextResponse.json({ error: auth.message }, { status: 401 });
  try {
    const { id } = await context.params;
    const body = await request.json().catch(() => ({})) as { parser?: TranscriptParserName };
    const parser = ["docling", "marker", "pymupdf"].includes(body.parser || "") ? body.parser! : "docling";
    const repository = new SupabaseTranscriptPipelineRepository(auth.client, auth.userId);
    const processed = await processStoredTranscript(repository, id, parser);
    return NextResponse.json({ data: { ...processed, detail: await repository.getDetailed(id) } });
  } catch (error) {
    return NextResponse.json({ error: "Transcript retry failed.", detail: error instanceof Error ? error.message : "Unknown error" }, { status: 422 });
  }
}
