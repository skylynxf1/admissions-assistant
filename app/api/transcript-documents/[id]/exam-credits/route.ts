import { NextResponse } from "next/server";
import { getBackendAuthContext } from "@/lib/backend/auth";
import { SupabaseTranscriptPipelineRepository } from "@/lib/backend/repositories/transcript-pipeline-repository";

type Context = { params: Promise<{ id: string }> };
export async function POST(request: Request, context: Context) {
  const auth = await getBackendAuthContext(request);
  if (auth.status === "unconfigured") return NextResponse.json({ error: "Supabase is not configured." }, { status: 503 });
  if (auth.status === "unauthorized") return NextResponse.json({ error: auth.message }, { status: 401 });
  try {
    const { id } = await context.params;
    const repository = new SupabaseTranscriptPipelineRepository(auth.client, auth.userId);
    return NextResponse.json({ data: await repository.addExamCredit(id, await request.json() as Record<string, unknown>) }, { status: 201 });
  } catch (error) {
    return NextResponse.json({ error: "Could not add exam credit.", detail: error instanceof Error ? error.message : "Unknown error" }, { status: 422 });
  }
}
