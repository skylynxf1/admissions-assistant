import { NextResponse } from "next/server";
import { getBackendAuthContext } from "@/lib/backend/auth";
import { SupabaseTranscriptPipelineRepository } from "@/lib/backend/repositories/transcript-pipeline-repository";

type Context = { params: Promise<{ id: string }> };

export async function GET(request: Request, context: Context) {
  const auth = await getBackendAuthContext(request);
  if (auth.status === "unconfigured") return NextResponse.json({ error: "Supabase is not configured." }, { status: 503 });
  if (auth.status === "unauthorized") return NextResponse.json({ error: auth.message }, { status: 401 });
  try {
    const { id } = await context.params;
    const repository = new SupabaseTranscriptPipelineRepository(auth.client, auth.userId);
    const data = await repository.getDetailed(id);
    return data ? NextResponse.json({ data }) : NextResponse.json({ error: "Transcript document not found." }, { status: 404 });
  } catch (error) {
    return NextResponse.json({ error: "Could not load transcript.", detail: error instanceof Error ? error.message : "Unknown error" }, { status: 500 });
  }
}

export async function DELETE(request: Request, context: Context) {
  const auth = await getBackendAuthContext(request);
  if (auth.status === "unconfigured") return NextResponse.json({ error: "Supabase is not configured." }, { status: 503 });
  if (auth.status === "unauthorized") return NextResponse.json({ error: auth.message }, { status: 401 });
  try {
    const { id } = await context.params;
    const repository = new SupabaseTranscriptPipelineRepository(auth.client, auth.userId);
    return (await repository.deleteDocument(id)) ? new NextResponse(null, { status: 204 }) : NextResponse.json({ error: "Transcript document not found." }, { status: 404 });
  } catch (error) {
    return NextResponse.json({ error: "Could not delete transcript.", detail: error instanceof Error ? error.message : "Unknown error" }, { status: 500 });
  }
}
