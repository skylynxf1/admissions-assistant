import type { SupabaseClient } from "@supabase/supabase-js";
import type { Database } from "@/lib/supabase/database.types";
import type { EvidenceIngestRequest } from "@/lib/backend/types";

export class SupabaseEvidenceRepository {
  constructor(private readonly adminClient: SupabaseClient<Database>) {}

  async ingest(request: EvidenceIngestRequest) {
    const pageResult = await this.adminClient.schema("source").from("pages").upsert({
      institution_id: request.institutionId,
      original_url: request.originalUrl,
      canonical_url: request.canonicalUrl,
      page_title: request.pageTitle ?? null,
      source_type: request.sourceType,
      official: request.official,
      active: true,
      last_seen_at: request.retrievedAt,
    }, { onConflict: "institution_id,canonical_url" }).select("id").single();
    if (pageResult.error || !pageResult.data) throw new Error(`Could not save source page: ${pageResult.error?.message ?? "No record returned"}`);

    const snapshotResult = await this.adminClient.schema("source").from("snapshots").upsert({
      page_id: pageResult.data.id,
      retrieved_at: request.retrievedAt,
      content_hash: request.contentHash,
      mime_type: request.mimeType ?? null,
      storage_bucket: request.storageBucket ?? null,
      storage_path: request.storagePath ?? null,
      http_status: request.httpStatus ?? null,
      catalog_year: request.catalogYear ?? null,
      effective_term: request.effectiveTerm ?? null,
      raw_text: request.rawText ?? null,
      response_metadata: request.responseMetadata ?? {},
    }, { onConflict: "page_id,content_hash" }).select("id").single();
    if (snapshotResult.error || !snapshotResult.data) throw new Error(`Could not save source snapshot: ${snapshotResult.error?.message ?? "No record returned"}`);

    const evidenceResult = request.evidence.length
      ? await this.adminClient.schema("source").from("evidence_records").insert(request.evidence.map((item) => ({
        snapshot_id: snapshotResult.data.id,
        parser_run_id: request.parserRunId ?? null,
        claim_key: item.claimKey,
        claim_type: item.claimType,
        exact_quote: item.exactQuote,
        locator: item.locator ?? {},
        table_headers: item.tableHeaders ?? null,
        table_row: item.tableRow ?? null,
        footnotes: item.footnotes ?? [],
        normalized_value: item.normalizedValue ?? null,
        effective_from: item.effectiveFrom ?? null,
        effective_to: item.effectiveTo ?? null,
        confidence: item.confidence,
        review_status: item.reviewStatus ?? "pending",
      }))).select("id")
      : { data: [], error: null };
    if (evidenceResult.error) throw new Error(`Could not save evidence records: ${evidenceResult.error.message}`);

    return { pageId: pageResult.data.id, snapshotId: snapshotResult.data.id, evidenceIds: (evidenceResult.data ?? []).map((item) => item.id) };
  }
}
