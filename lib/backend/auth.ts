import "server-only";
import type { SupabaseClient } from "@supabase/supabase-js";
import { getSupabaseConfiguration, getSupabaseUserClient } from "@/lib/supabase/server";
import type { Database } from "@/lib/supabase/database.types";

export type BackendAuthContext =
  | { status: "ready"; client: SupabaseClient<Database>; userId: string; accessToken: string }
  | { status: "unconfigured" }
  | { status: "unauthorized"; message: string };

function readBearerToken(request: Request) {
  const authorization = request.headers.get("authorization");
  if (!authorization?.startsWith("Bearer ")) return null;
  return authorization.slice("Bearer ".length).trim() || null;
}

export async function getBackendAuthContext(request: Request): Promise<BackendAuthContext> {
  if (!getSupabaseConfiguration().publicConfigured) return { status: "unconfigured" };
  const accessToken = readBearerToken(request);
  if (!accessToken) return { status: "unauthorized", message: "A Supabase access token is required." };
  const client = getSupabaseUserClient(accessToken);
  if (!client) return { status: "unconfigured" };
  const { data, error } = await client.auth.getUser(accessToken);
  if (error || !data.user) return { status: "unauthorized", message: "The Supabase session is invalid or expired." };
  return { status: "ready", client, userId: data.user.id, accessToken };
}
