import "server-only";
import OpenAI from "openai";

let client: OpenAI | null | undefined;

export function getOpenAIClient(): OpenAI | null {
  if (client !== undefined) return client;
  const apiKey = process.env.OPENAI_API_KEY;
  client = apiKey ? new OpenAI({ apiKey }) : null;
  return client;
}

export function getConfiguredModel(): string {
  return process.env.OPENAI_MODEL || "gpt-5.6";
}
