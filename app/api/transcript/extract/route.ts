import { NextResponse } from "next/server";
import { academicPlanningServices } from "@/lib/services";
import { getConfiguredModel, getOpenAIClient } from "@/lib/openai";

export async function POST(request: Request) {
  try {
    const formData = await request.formData();
    const file = formData.get("transcript");
    const fileName = file instanceof File ? file.name : "sample-transfer-transcript.pdf";

    // GPT-5.6 TODO: send the PDF as a file input and require the TranscriptData schema as structured output.
    const transcript = await academicPlanningServices.transcriptParser.parse(fileName);
    return NextResponse.json({
      data: transcript,
      meta: { mode: "mock", modelConfigured: Boolean(getOpenAIClient()), intendedModel: getConfiguredModel() },
    });
  } catch (error) {
    return NextResponse.json({ error: "Transcript extraction failed", detail: error instanceof Error ? error.message : "Unknown error" }, { status: 400 });
  }
}
