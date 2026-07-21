import assert from "node:assert/strict";
import test from "node:test";
import { fetchTransferOutcomes } from "../lib/transfer/client.ts";
import type { TransferOutcomeRequest, TransferOutcomeResponse } from "../lib/transfer/types.ts";

const sampleRequest: TransferOutcomeRequest = {
  pathway_key: "bellevue-uw-cse",
  courses: [{ code: "CS 142", title: "Computer Science I" }],
};

const sampleResponse: TransferOutcomeResponse = {
  pathway_key: "bellevue-uw-cse",
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

test("fetchTransferOutcomes posts to the outcomes endpoint and returns the parsed body", async () => {
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

  const result = await fetchTransferOutcomes(sampleRequest, {
    baseUrl: "http://127.0.0.1:8000",
    fetchImpl: fetchImpl as typeof fetch,
  });

  assert.equal(capturedUrl, "http://127.0.0.1:8000/transfer/outcomes");
  assert.equal(capturedInit?.method, "POST");
  assert.equal(capturedInit?.headers && (capturedInit.headers as Record<string, string>)["Content-Type"], "application/json");
  assert.deepEqual(JSON.parse(capturedInit?.body as string), sampleRequest);
  assert.deepEqual(result, sampleResponse);
});

test("throws a clear configuration error when no base URL is available", async () => {
  const originalEnv = process.env.ACADEMIC_INGEST_SERVICE_URL;
  delete process.env.ACADEMIC_INGEST_SERVICE_URL;
  try {
    await assert.rejects(
      () => fetchTransferOutcomes(sampleRequest, { fetchImpl: (async () => new Response("{}")) as unknown as typeof fetch }),
      /ACADEMIC_INGEST_SERVICE_URL is not configured/,
    );
  } finally {
    if (originalEnv === undefined) delete process.env.ACADEMIC_INGEST_SERVICE_URL;
    else process.env.ACADEMIC_INGEST_SERVICE_URL = originalEnv;
  }
});

test("throws an Error including the status code on a non-2xx upstream response", async () => {
  const fetchImpl = async () => new Response("Internal error", { status: 500 });
  await assert.rejects(
    () => fetchTransferOutcomes(sampleRequest, { baseUrl: "http://127.0.0.1:8000", fetchImpl: fetchImpl as typeof fetch }),
    /500/,
  );
});
