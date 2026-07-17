import { NextResponse } from "next/server";
import { getSupabaseConfiguration } from "@/lib/supabase/server";

export async function GET() {
  const configuration = getSupabaseConfiguration();
  return NextResponse.json({
    data: {
      status: configuration.publicConfigured ? "configured" : "demo-fallback",
      publicClient: configuration.publicConfigured,
      trustedIngestion: configuration.adminConfigured && Boolean(process.env.INGESTION_API_KEY),
      domains: ["source", "catalog", "policy", "equivalency", "student", "planning", "operations"],
      migrations: ["202607160001_initial_backend.sql"],
    },
    meta: { secretsExposed: false },
  });
}
