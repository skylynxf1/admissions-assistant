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

  const fetchImpl = opts.fetchImpl ?? fetch;
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
