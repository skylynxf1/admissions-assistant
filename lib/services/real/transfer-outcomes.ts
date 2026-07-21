import type {
  TransferOutcomeRequestInput,
  TransferOutcomeService,
  TransferOutcomeServiceResult,
} from "@/lib/services/interfaces";
import type { TransferOutcomeResponse } from "@/lib/transfer/types";

export interface RealTransferOutcomeServiceOptions {
  // Same-origin Next.js route path. Never call the Python academic-ingest service
  // directly from the browser.
  endpoint?: string;
  // Injected for tests so they never hit the network; defaults to global fetch.
  fetchImpl?: typeof fetch;
}

// REAL IMPLEMENTATION: calls POST /api/transfer/outcomes, which proxies to the Python
// academic-ingest resolver. Pure function of its input — course codes are passed in by
// the caller, never read from React context, localStorage, or other app state.
export class RealTransferOutcomeService implements TransferOutcomeService {
  private readonly endpoint: string;
  private readonly fetchImpl: typeof fetch;

  constructor(options: RealTransferOutcomeServiceOptions = {}) {
    this.endpoint = options.endpoint ?? "/api/transfer/outcomes";
    // Wrap (rather than assign bare `fetch`) so the default still works when called as
    // `this.fetchImpl(...)` — native fetch requires `this` to be the global object, and
    // storing the bare function on an instance detaches it, which browsers reject with
    // "Illegal invocation".
    this.fetchImpl = options.fetchImpl ?? ((input, init) => globalThis.fetch(input, init));
  }

  async resolve(input: TransferOutcomeRequestInput): Promise<TransferOutcomeServiceResult> {
    let response: Response;
    try {
      response = await this.fetchImpl(this.endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          pathway_key: input.pathwayKey,
          courses: input.courses,
        }),
      });
    } catch (error) {
      return {
        available: false,
        unavailableReason: error instanceof Error ? error.message : "Transfer outcomes service is unavailable.",
        outcomes: [],
      };
    }

    if (!response.ok) {
      return {
        available: false,
        unavailableReason: await this.describeError(response),
        outcomes: [],
      };
    }

    const body = (await response.json()) as TransferOutcomeResponse;
    return { available: true, outcomes: body.outcomes };
  }

  private async describeError(response: Response): Promise<string> {
    try {
      const body = (await response.json()) as { error?: string };
      if (typeof body?.error === "string" && body.error.trim() !== "") return body.error;
    } catch {
      // Body was not JSON (or empty) — fall back to the status code below.
    }
    return `Transfer outcomes service responded with status ${response.status}.`;
  }
}
