import { NextResponse } from "next/server";
import { academicPlanningServices } from "@/lib/services";
import { getConfiguredModel, getOpenAIClient } from "@/lib/openai";
import type { AcademicAnalysisInput } from "@/lib/types";

export async function POST(request: Request) {
  try {
    const input = (await request.json()) as AcademicAnalysisInput;
    if (!input.profile || !input.transcript || !input.scenario || !Array.isArray(input.targets)) {
      return NextResponse.json({ error: "Invalid academic analysis input" }, { status: 422 });
    }

    // GPT-5.6 TODO: retrieve versioned policies, then use structured reasoning only for interpretation.
    const analysis = await academicPlanningServices.scenarioSimulator.simulate(input);
    return NextResponse.json({
      data: analysis,
      meta: { mode: "mock", modelConfigured: Boolean(getOpenAIClient()), intendedModel: getConfiguredModel() },
    });
  } catch (error) {
    return NextResponse.json({ error: "Academic analysis failed", detail: error instanceof Error ? error.message : "Unknown error" }, { status: 400 });
  }
}
