import assert from "node:assert/strict";
import test from "node:test";
import { RealTransferOutcomeService } from "../lib/services/real/transfer-outcomes.ts";
import { MockTransferOutcomeService } from "../lib/services/mock.ts";
import type { TransferOutcomeResponse } from "../lib/transfer/types.ts";

const sampleResponse: TransferOutcomeResponse = {
  pathway_key: "bellevue-college:uw-seattle",
  source_institution_id: "bellevue-college",
  destination_institution_id: "university-of-washington",
  outcomes: [
    {
      source_course: { code: "CS 142", title: "Computer Science I" },
      state: "resolved",
      destination_outcomes: ["CSE 142"],
      credits_awarded: 5,
      minimum_grade: "2.0",
      conditions: {},
      evidence_refs: ["evidence-1"],
      detail: null,
    },
  ],
};

test("RealTransferOutcomeService.resolve posts to /api/transfer/outcomes and returns available outcomes", async () => {
  let capturedUrl: string | undefined;
  let capturedInit: RequestInit | undefined;
  const fetchImpl = async (input: string | URL | Request, init?: RequestInit) => {
    capturedUrl = String(input);
    capturedInit = init;
    return new Response(JSON.stringify(sampleResponse), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
  };

  const service = new RealTransferOutcomeService({ fetchImpl: fetchImpl as typeof fetch });
  const result = await service.resolve({
    pathwayKey: "bellevue-college:uw-seattle",
    courses: [{ code: "CS 142", title: "Computer Science I" }],
  });

  assert.equal(capturedUrl, "/api/transfer/outcomes");
  assert.equal(capturedInit?.method, "POST");
  assert.equal(capturedInit?.headers && (capturedInit.headers as Record<string, string>)["Content-Type"], "application/json");
  assert.deepEqual(JSON.parse(capturedInit?.body as string), {
    pathway_key: "bellevue-college:uw-seattle",
    courses: [{ code: "CS 142", title: "Computer Science I" }],
  });
  assert.deepEqual(result, { available: true, outcomes: sampleResponse.outcomes });
});

test("RealTransferOutcomeService.resolve reports unavailable on a 503 response without throwing", async () => {
  const fetchImpl = async () => new Response(JSON.stringify({ error: "Transfer outcomes service is unavailable" }), {
    status: 503,
    headers: { "content-type": "application/json" },
  });

  const service = new RealTransferOutcomeService({ fetchImpl: fetchImpl as typeof fetch });
  const result = await service.resolve({
    pathwayKey: "bellevue-college:uw-seattle",
    courses: [{ code: "CS 142" }],
  });

  assert.equal(result.available, false);
  assert.equal(result.unavailableReason, "Transfer outcomes service is unavailable");
  assert.deepEqual(result.outcomes, []);
});

test("RealTransferOutcomeService.resolve reports unavailable using the status code when the body has no message", async () => {
  const fetchImpl = async () => new Response("", { status: 503 });

  const service = new RealTransferOutcomeService({ fetchImpl: fetchImpl as typeof fetch });
  const result = await service.resolve({
    pathwayKey: "bellevue-college:uw-seattle",
    courses: [{ code: "CS 142" }],
  });

  assert.equal(result.available, false);
  assert.match(result.unavailableReason ?? "", /503/);
  assert.deepEqual(result.outcomes, []);
});

test("RealTransferOutcomeService.resolve works with the default fetch (no injected fetchImpl)", async () => {
  const originalFetch = globalThis.fetch;
  const calls: Array<{ input: unknown; init: unknown }> = [];

  // A regular (non-arrow) function so `this` inside it reflects how it was invoked —
  // just like native browser fetch, which throws "Illegal invocation" when called as
  // a detached method (`this.fetchImpl(...)`) instead of `globalThis.fetch(...)`.
  // This reproduces the real bug without touching the network: if the service still
  // stores the bare `fetch` reference on `this.fetchImpl`, this stub's `this` binding
  // will be the service instance rather than globalThis, and the assertion below fails.
  function stubFetch(this: unknown, input: unknown, init: unknown) {
    if (this !== globalThis) {
      throw new TypeError("Failed to execute 'fetch' on 'Window': Illegal invocation");
    }
    calls.push({ input, init });
    return Promise.resolve({
      ok: true,
      status: 200,
      json: async () => sampleResponse,
    });
  }

  // @ts-expect-error -- stub is intentionally not a full fetch implementation
  globalThis.fetch = stubFetch;

  try {
    // No fetchImpl passed in: this exercises the default `fetch` path, which is the
    // one the browser actually uses and the one the old bare `fetch` assignment broke.
    const service = new RealTransferOutcomeService();
    const result = await service.resolve({
      pathwayKey: "bellevue-college:uw-seattle",
      courses: [{ code: "CS 142", title: "Computer Science I" }],
    });

    assert.equal(calls.length, 1);
    assert.deepEqual(result, { available: true, outcomes: sampleResponse.outcomes });
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("MockTransferOutcomeService.resolve reports not enabled without fabricating outcomes", async () => {
  const service = new MockTransferOutcomeService();
  const result = await service.resolve({
    pathwayKey: "bellevue-college:uw-seattle",
    courses: [{ code: "CS 142" }],
  });

  assert.equal(result.available, false);
  assert.equal(result.unavailableReason, "Live transfer service is not enabled.");
  assert.deepEqual(result.outcomes, []);
});
