import { NextResponse } from "next/server";
import { academicPlanningServices } from "@/lib/services";
import { getConfiguredModel, getOpenAIClient } from "@/lib/openai";
import type { AcademicAnalysisInput } from "@/lib/types";

export async function POST(request: Request) {
  try {
    const input = (await request.json()) as AcademicAnalysisInput;
    if (!input.scenario || !input.transcript || !Array.isArray(input.targets)) {
      return NextResponse.json({ error: "Invalid simulation input" }, { status: 422 });
    }

    // GPT-5.6 TODO: use the same grounded policy bundle while varying only explicit scenario inputs.
    const result = await academicPlanningServices.scenarioSimulator.simulate(input);
    return NextResponse.json({
      data: result,
      meta: { mode: "mock", modelConfigured: Boolean(getOpenAIClient()), intendedModel: getConfiguredModel() },
    });
  } catch (error) {
    return NextResponse.json({ error: "Scenario simulation failed", detail: error instanceof Error ? error.message : "Unknown error" }, { status: 400 });
  }
}
