import { NextResponse } from "next/server";
import { getBackendAuthContext } from "@/lib/backend/auth";
import { SupabaseTranscriptPipelineRepository } from "@/lib/backend/repositories/transcript-pipeline-repository";

type Context = { params: Promise<{ id: string; warningId: string }> };
export async function PATCH(request: Request, context: Context) {
  const auth = await getBackendAuthContext(request);
  if (auth.status === "unconfigured") return NextResponse.json({ error: "Supabase is not configured." }, { status: 503 });
  if (auth.status === "unauthorized") return NextResponse.json({ error: auth.message }, { status: 401 });
  try {
    const { id, warningId } = await context.params;
    const body = await request.json() as { state?: "resolved" | "dismissed"; note?: string };
    if (body.state !== "resolved" && body.state !== "dismissed") return NextResponse.json({ error: "State must be resolved or dismissed." }, { status: 422 });
    const repository = new SupabaseTranscriptPipelineRepository(auth.client, auth.userId);
    return NextResponse.json({ data: await repository.resolveWarning(id, warningId, body.state, body.note) });
  } catch (error) {
    return NextResponse.json({ error: "Could not resolve warning.", detail: error instanceof Error ? error.message : "Unknown error" }, { status: 422 });
  }
}
