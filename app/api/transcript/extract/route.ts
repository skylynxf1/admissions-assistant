import { NextResponse } from "next/server";
import { getConfiguredModel, getOpenAIClient } from "@/lib/openai";
import { createSamplePipelineResult, validatedTranscriptToPlannerData } from "@/lib/transcript/sample";
import { runTranscriptPipeline } from "@/lib/transcript/pipeline";
import { validateTranscriptPdf } from "@/lib/transcript/pdf-validation";

export async function POST(request: Request) {
  try {
    const formData = await request.formData();
    const formFile = formData.get("transcript");
    const file = formFile instanceof File ? formFile : null;
    if (file) {
      const validation = await validateTranscriptPdf(file);
      if (!validation.ok) return NextResponse.json({ error: validation.message, code: validation.code }, { status: 422 });
    }

    const liveConfigured = Boolean(file && process.env.DOCLING_SERVICE_URL && getOpenAIClient());
    const pipeline = liveConfigured && file
      ? await runTranscriptPipeline(file)
      : createSamplePipelineResult(file?.name ?? "sample-transfer-transcript.pdf");
    const transcript = validatedTranscriptToPlannerData(pipeline.validatedTranscript, pipeline.documentId, pipeline.fileName);
    return NextResponse.json({
      data: transcript,
      pipeline,
      meta: {
        mode: pipeline.mode,
        modelConfigured: Boolean(getOpenAIClient()),
        parserConfigured: Boolean(process.env.DOCLING_SERVICE_URL),
        intendedModel: getConfiguredModel(),
        notice: pipeline.mode === "sample" ? "Sample extraction data — not read from the uploaded PDF." : null,
      },
    });
  } catch (error) {
    return NextResponse.json({ error: "Transcript extraction failed", detail: error instanceof Error ? error.message : "Unknown error" }, { status: 400 });
  }
}
