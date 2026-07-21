import type { TransferOutcomeRequest, TransferOutcomeResponse } from "@/lib/transfer/types";

export interface FetchTransferOutcomesOptions {
  baseUrl?: string;
  fetchImpl?: typeof fetch;
}

export async function fetchTransferOutcomes(
  req: TransferOutcomeRequest,
  opts: FetchTransferOutcomesOptions = {},
): Promise<TransferOutcomeResponse> {
  const baseUrl = opts.baseUrl ?? process.env.ACADEMIC_INGEST_SERVICE_URL;
  if (!baseUrl) throw new Error("ACADEMIC_INGEST_SERVICE_URL is not configured");

  // Wrap (rather than assign bare `fetch`) so the default doesn't rely on the receiver
  // being the global object — same detached-`this` hazard as the browser-side service.
  const fetchImpl = opts.fetchImpl ?? ((input, init) => globalThis.fetch(input, init));
  const response = await fetchImpl(`${baseUrl.replace(/\/$/, "")}/transfer/outcomes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });

  if (!response.ok) {
    const body = await response.text().catch(() => "");
    throw new Error(`Transfer outcomes request failed with status ${response.status}${body ? `: ${body}` : ""}`);
  }

  return response.json() as Promise<TransferOutcomeResponse>;
}
