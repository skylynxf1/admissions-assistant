# GPT-5.6 connection TODO

The prototype deliberately runs on labeled sample data. Connect production intelligence in this order:

1. **Structured transcript extraction**
   - Send uploaded PDFs to the transcript route as file inputs.
   - Require the `TranscriptData` schema as structured output.
   - Store page references and field-level confidence; never silently overwrite user edits.

2. **Versioned policy retrieval**
   - Crawl only official university, registrar, catalog, department, articulation, and exam-credit sources.
   - Store source URL, effective term, retrieval time, content hash, and supersession status.
   - Retrieve a bounded source bundle for every selected school and major.

3. **Grounded academic analysis**
   - Keep credit arithmetic, duplicate detection, prerequisite traversal, and requirement totals deterministic.
   - Use GPT-5.6 for ambiguous policy interpretation, footnotes, cross-source conflicts, and explanations.
   - Require strict `AnalysisResult` output and reject uncited policy conclusions.

4. **Scenario simulation**
   - Reuse the same source bundle and change only explicit scenario fields.
   - Add regression fixtures proving that credit totals and prerequisite states remain deterministic.

5. **Advisor chat**
   - Ground every answer in the saved transcript, selected scenario, analysis, and policy bundle.
   - Return facts, estimates, assumptions, citations, confidence, and escalation advice separately.

6. **Trust and operations**
   - Add policy freshness jobs, source conflict detection, moderation, PII retention controls, audit logs, cost limits, rate limiting, and human evaluation.
   - Keep the sample-data banner until a scenario has complete, current, official-source coverage.

Server boundaries already exist at `/api/transcript/extract`, `/api/academic-analysis`, `/api/simulation`, and `/api/advisor`. `OPENAI_API_KEY` and `OPENAI_MODEL` are read server-side but do not trigger live calls yet.
