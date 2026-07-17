import "server-only";
import { transcriptExtractionJsonSchema } from "@/lib/transcript/extraction-schema";
import type { TranscriptStructuredExtractor } from "@/lib/transcript/extractors/interface";
import type { ParsedTranscriptDocument, TranscriptExtraction } from "@/lib/transcript/types";
import { getConfiguredModel, getOpenAIClient } from "@/lib/openai";

export class OpenAITranscriptExtractor implements TranscriptStructuredExtractor {
  async extract(document: ParsedTranscriptDocument): Promise<TranscriptExtraction> {
    const client = getOpenAIClient();
    if (!client) throw new Error("OPENAI_API_KEY is not configured.");

    const response = await client.responses.create({
      model: getConfiguredModel(),
      instructions: [
        "Extract only facts explicitly printed in this college transcript.",
        "Never infer transferability, course equivalency, degree applicability, prerequisites, or destination-school policy.",
        "Use null for an unknown scalar and an empty array when a collection is absent.",
        "Keep distinct institutions and academic terms. Preserve repeated courses as separate rows.",
        "Cite the one-based PDF page and parser block IDs supporting every extracted entity.",
        "Confidence is a 0 to 1 estimate of transcription certainty, not academic validity.",
      ].join(" "),
      input: `Parser: ${document.parser} ${document.parserVersion}\nPages: ${document.pageCount}\n\n${document.markdown}`,
      text: {
        format: {
          type: "json_schema",
          name: "transcript_extraction",
          strict: true,
          schema: transcriptExtractionJsonSchema,
        },
      },
    });

    if (!response.output_text) throw new Error("The extraction model returned no structured output.");
    return JSON.parse(response.output_text) as TranscriptExtraction;
  }
}
