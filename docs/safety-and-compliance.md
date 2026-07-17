# Safety, privacy, and compliance

## Network and access controls

- Network access is disabled by default and needs explicit operator opt-in.
- Live requests use only configured official HTTPS hosts and a contact-bearing user agent.
- DNS results must be globally routable; IP literals, loopback, link-local, and private targets fail.
- Redirect destinations are revalidated. Response types and sizes are bounded.
- Robots policy is evaluated before target inspection; unavailable policy fails closed.
- Per-host rate limits, bounded concurrency, retries/backoff, ETags, and Last-Modified reduce load.
- Authenticated and NetID-protected resources are outside scope. The system does not bypass controls.

## Untrusted content

All fetched pages, PDFs, table cells, links, and model output are untrusted. HTML is parsed as data and
scripts are not executed. PDF pages and model input are bounded. Discovered links pass canonical URL,
domain, campus, and access-policy checks before acquisition.

Model-assisted extraction receives no credentials and no arbitrary browsing capability. Prompts
instruct it to use only supplied content, but deterministic schema, URL, evidence, logical, conflict,
and confidence gates remain authoritative.

## Evidence integrity and retention

Snapshots are immutable and content addressed. Normalized claims cite exact snapshot text and retain
structural context. Historical evidence and versions are never mutated in place. Reviewer decisions
append resolution metadata.

Production deployments should set a documented retention period for snapshot objects, database
backups, exports, and logs. Deletion policy must preserve referential integrity or explicitly tombstone
records; do not silently leave published claims without evidence.

Exports contain normalized records, evidence text, source metadata, hashes, and content locations but
exclude raw page bytes. Access to snapshots may still expose copyrighted or sensitive page content and
should follow least privilege.

## Privacy and secrets

The UW ingestion sources are public institutional pages; student records are not part of this adapter.
Do not place transcripts, applicant PII, API keys, database credentials, cookies, authorization
headers, or private URLs in fixtures, prompts, logs, review questions, or exports.

Secrets belong in environment/secret management. Structured logs include job/source/request IDs,
model ID, prompt/schema versions, usage, counts, retry count, and validation disposition—not page
bodies or full model requests.

## Human review

Review is required for missing/unverifiable evidence, ambiguity, unresolved fields, conflicting
official claims, critical material changes, unclear effective periods when consequential, and any
unsupported no-credit or equivalency interpretation. A reviewer should compare exact sources, scope,
authority, and dates and record rationale without deleting the original evidence.
