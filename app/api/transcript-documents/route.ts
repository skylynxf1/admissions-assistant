import { NextResponse } from "next/server";
import { getBackendAuthContext } from "@/lib/backend/auth";
import { SupabaseTranscriptPipelineRepository } from "@/lib/backend/repositories/transcript-pipeline-repository";
import { validateTranscriptPdf } from "@/lib/transcript/pdf-validation";

export async function GET(request: Request) {
  const auth = await getBackendAuthContext(request);
  if (auth.status === "unconfigured") return NextResponse.json({ error: "Supabase is not configured." }, { status: 503 });
  if (auth.status === "unauthorized") return NextResponse.json({ error: auth.message }, { status: 401 });
  try {
    const repository = new SupabaseTranscriptPipelineRepository(auth.client, auth.userId);
    return NextResponse.json({ data: await repository.list() });
  } catch (error) {
    return NextResponse.json({ error: "Could not list transcript documents.", detail: error instanceof Error ? error.message : "Unknown error" }, { status: 500 });
  }
}

export async function POST(request: Request) {
  const auth = await getBackendAuthContext(request);
  if (auth.status === "unconfigured") return NextResponse.json({ error: "Supabase is not configured." }, { status: 503 });
  if (auth.status === "unauthorized") return NextResponse.json({ error: auth.message }, { status: 401 });
  try {
    const form = await request.formData();
    const entry = form.get("transcript");
    const file = entry instanceof File ? entry : null;
    const validation = await validateTranscriptPdf(file);
    if (!validation.ok) return NextResponse.json({ error: validation.message, code: validation.code }, { status: 422 });
    const repository = new SupabaseTranscriptPipelineRepository(auth.client, auth.userId);
    const duplicate = await repository.findDuplicate(validation.sha256);
    if (duplicate) return NextResponse.json({ error: "This transcript PDF has already been uploaded.", code: "duplicate_pdf", data: duplicate }, { status: 409 });
    return NextResponse.json({ data: await repository.upload(file!, validation.sha256) }, { status: 201 });
  } catch (error) {
    return NextResponse.json({ error: "Could not upload transcript.", detail: error instanceof Error ? error.message : "Unknown error" }, { status: 500 });
  }
}
