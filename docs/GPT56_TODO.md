# GPT-5.6 connection TODO

The prototype deliberately runs on labeled sample data. Connect production intelligence in this order:

1. **Structured transcript extraction — scaffold complete**
   - Private upload, Docling adapter, strict structured output, deterministic validation, page evidence, retry audit, editable normalization, and no-key fallback are implemented.
   - Before production, move processing to a durable queue, add virus scanning and retention controls, and evaluate extraction quality on redacted real-world layouts.

2. **Versioned policy retrieval**
   - Crawl only official university, registrar, catalog, department, articulation, and exam-credit sources.
   - Store source URL, effective term, retrieval time, content hash, and supersession status.
   - Retrieve a bounded source bundle for every selected school and major.
   - Write scraped pages, snapshots, parser runs, and exact claims through the trusted evidence-ingestion repository.
   - Promote reviewed claims into `catalog`, `policy`, or `equivalency` rows without mutating the source snapshot.

3. **Grounded academic analysis**
   - Keep credit arithmetic, duplicate detection, prerequisite traversal, and requirement totals deterministic.
   - Use GPT-5.6 for ambiguous policy interpretation, footnotes, cross-source conflicts, and explanations.
   - Require strict `AnalysisResult` output and reject uncited policy conclusions.
   - Preserve the five verification states and require an explicit source check before a destination course mapping can be returned.
   - Route unresolved and conflicting items through the existing exact-course, institution, term, question, office, and draft-email model.

4. **Scenario simulation**
   - Reuse the same source bundle and change only explicit scenario fields.
   - Add regression fixtures proving that credit totals and prerequisite states remain deterministic.

5. **Advisor chat**
   - Ground every answer in the saved transcript, selected scenario, analysis, and policy bundle.
   - Return facts, estimates, assumptions, citations, confidence, and escalation advice separately.

6. **Trust and operations**
   - Add policy freshness jobs, source conflict detection, moderation, PII retention controls, audit logs, cost limits, rate limiting, and human evaluation.
   - Keep the sample-data banner until a scenario has complete, current, official-source coverage.

Server boundaries exist at `/api/transcript/extract`, `/api/transcript-documents/*`, `/api/academic-analysis`, `/api/simulation`, and `/api/advisor`. OpenAI triggers live transcript extraction only when `DOCLING_SERVICE_URL` is also configured; academic-policy reasoning remains sample-only.
