import { NextResponse } from "next/server";
import { academicPlanningServices } from "@/lib/services";
import { getConfiguredModel, getOpenAIClient } from "@/lib/openai";
import type { AdvisorInput } from "@/lib/types";

export async function POST(request: Request) {
  try {
    const input = (await request.json()) as AdvisorInput;
    if (!input.question?.trim() || !input.analysis || !input.transcript) {
      return NextResponse.json({ error: "Question and academic context are required" }, { status: 422 });
    }

    // GPT-5.6 TODO: send the full scenario context and require citations, assumptions, and confidence fields.
    const answer = await academicPlanningServices.advisorChat.answer(input);
    return NextResponse.json({
      data: answer,
      meta: { mode: "mock", modelConfigured: Boolean(getOpenAIClient()), intendedModel: getConfiguredModel() },
    });
  } catch (error) {
    return NextResponse.json({ error: "Advisor response failed", detail: error instanceof Error ? error.message : "Unknown error" }, { status: 400 });
  }
}
