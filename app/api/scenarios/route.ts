import { NextResponse } from "next/server";
import { getBackendAuthContext } from "@/lib/backend/auth";
import { isSaveScenarioRequest } from "@/lib/backend/types";
import { SupabaseScenarioRepository } from "@/lib/backend/repositories/scenario-repository";
import { getSupabaseAdminClient } from "@/lib/supabase/server";

function authFailure(status: "unconfigured" | "unauthorized", message?: string) {
  return NextResponse.json(
    { error: status === "unconfigured" ? "Supabase is not configured." : message },
    { status: status === "unconfigured" ? 503 : 401 },
  );
}

export async function GET(request: Request) {
  const auth = await getBackendAuthContext(request);
  if (auth.status !== "ready") return authFailure(auth.status, auth.status === "unauthorized" ? auth.message : undefined);
  try {
    const repository = new SupabaseScenarioRepository(auth.client, auth.userId, getSupabaseAdminClient());
    return NextResponse.json({ data: await repository.list(), meta: { mode: "supabase" } });
  } catch (error) {
    return NextResponse.json({ error: "Could not load scenarios", detail: error instanceof Error ? error.message : "Unknown error" }, { status: 500 });
  }
}

export async function POST(request: Request) {
  const auth = await getBackendAuthContext(request);
  if (auth.status !== "ready") return authFailure(auth.status, auth.status === "unauthorized" ? auth.message : undefined);
  try {
    const body: unknown = await request.json();
    if (!isSaveScenarioRequest(body)) return NextResponse.json({ error: "Invalid scenario payload" }, { status: 422 });
    const repository = new SupabaseScenarioRepository(auth.client, auth.userId, getSupabaseAdminClient());
    return NextResponse.json({ data: await repository.save(body), meta: { mode: "supabase" } }, { status: 201 });
  } catch (error) {
    return NextResponse.json({ error: "Could not save scenario", detail: error instanceof Error ? error.message : "Unknown error" }, { status: 500 });
  }
}
