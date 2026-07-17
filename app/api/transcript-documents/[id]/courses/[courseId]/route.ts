import { NextResponse } from "next/server";
import { getBackendAuthContext } from "@/lib/backend/auth";
import { SupabaseTranscriptPipelineRepository } from "@/lib/backend/repositories/transcript-pipeline-repository";

type Context = { params: Promise<{ id: string; courseId: string }> };
export async function PATCH(request: Request, context: Context) {
  const auth = await getBackendAuthContext(request);
  if (auth.status === "unconfigured") return NextResponse.json({ error: "Supabase is not configured." }, { status: 503 });
  if (auth.status === "unauthorized") return NextResponse.json({ error: auth.message }, { status: 401 });
  try {
    const { id, courseId } = await context.params;
    const repository = new SupabaseTranscriptPipelineRepository(auth.client, auth.userId);
    return NextResponse.json({ data: await repository.updateCourse(id, courseId, await request.json() as Record<string, unknown>) });
  } catch (error) {
    return NextResponse.json({ error: "Could not update course.", detail: error instanceof Error ? error.message : "Unknown error" }, { status: 422 });
  }
}

export async function DELETE(request: Request, context: Context) {
  const auth = await getBackendAuthContext(request);
  if (auth.status === "unconfigured") return NextResponse.json({ error: "Supabase is not configured." }, { status: 503 });
  if (auth.status === "unauthorized") return NextResponse.json({ error: auth.message }, { status: 401 });
  try {
    const { id, courseId } = await context.params;
    const repository = new SupabaseTranscriptPipelineRepository(auth.client, auth.userId);
    await repository.deleteCourse(id, courseId);
    return new NextResponse(null, { status: 204 });
  } catch (error) {
    return NextResponse.json({ error: "Could not delete course.", detail: error instanceof Error ? error.message : "Unknown error" }, { status: 422 });
  }
}
