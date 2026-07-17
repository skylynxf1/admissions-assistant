import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { normalizeTranscriptExtraction } from "../lib/transcript/normalizer.ts";
import { validateTranscriptExtraction } from "../lib/transcript/validator.ts";
import type { TranscriptExtraction } from "../lib/transcript/types.ts";

const fixture = JSON.parse(readFileSync(new URL("./fixtures/sample-transcript-extraction.json", import.meta.url), "utf8")) as TranscriptExtraction;

test("normalization is deterministic and does not create academic conclusions", () => {
  const normalized = normalizeTranscriptExtraction(fixture);
  assert.equal(normalized.courses[0].courseCode, "MATH 101");
  assert.equal(normalized.courses[0].courseTitle, "College Algebra");
  assert.equal(normalized.courses[0].grade, "A");
  assert.equal("destinationCourse" in normalized.courses[0], false);
});

test("a consistent extraction validates without warnings", () => {
  const result = validateTranscriptExtraction(normalizeTranscriptExtraction(fixture), 1);
  assert.equal(result.metrics.courseCount, 1);
  assert.equal(result.metrics.calculatedEarnedCredits, 5);
  assert.equal(result.metrics.blockingWarningCount, 0);
  assert.deepEqual(result.warnings, []);
});

test("validation flags impossible credits, low confidence, and invalid page evidence", () => {
  const extraction = structuredClone(fixture);
  extraction.courses[0].creditsAttempted = 3;
  extraction.courses[0].creditsEarned = 5;
  extraction.courses[0].confidence = 0.4;
  extraction.courses[0].source.pageNumber = 2;
  const result = validateTranscriptExtraction(extraction, 1);
  const codes = new Set(result.warnings.map((warning) => warning.code));
  assert.equal(codes.has("earned_exceeds_attempted"), true);
  assert.equal(codes.has("low_confidence"), true);
  assert.equal(codes.has("invalid_source_page"), true);
  assert.equal(result.requiresReview, true);
});

test("validation preserves repeated rows and warns instead of silently deduplicating", () => {
  const extraction = structuredClone(fixture);
  extraction.courses.push({ ...structuredClone(extraction.courses[0]), id: "course-2" });
  const result = validateTranscriptExtraction(extraction, 1);
  assert.equal(result.extraction.courses.length, 2);
  assert.equal(result.warnings.some((warning) => warning.code === "possible_duplicate"), true);
});
