import { NextResponse } from "next/server";
import { getBackendAuthContext } from "@/lib/backend/auth";
import { isSaveTranscriptRequest } from "@/lib/backend/types";
import { SupabaseTranscriptRepository } from "@/lib/backend/repositories/transcript-repository";

export async function POST(request: Request) {
  const auth = await getBackendAuthContext(request);
  if (auth.status === "unconfigured") return NextResponse.json({ error: "Supabase is not configured." }, { status: 503 });
  if (auth.status === "unauthorized") return NextResponse.json({ error: auth.message }, { status: 401 });
  try {
    const body: unknown = await request.json();
    if (!isSaveTranscriptRequest(body)) return NextResponse.json({ error: "Invalid transcript payload" }, { status: 422 });
    const repository = new SupabaseTranscriptRepository(auth.client, auth.userId);
    return NextResponse.json({ data: await repository.save(body), meta: { mode: "supabase" } }, { status: 201 });
  } catch (error) {
    return NextResponse.json({ error: "Could not save transcript", detail: error instanceof Error ? error.message : "Unknown error" }, { status: 500 });
  }
}
