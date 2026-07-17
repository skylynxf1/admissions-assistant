from __future__ import annotations

import argparse
import json
import os
from collections.abc import Sequence
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from academic_ingest.config.settings import load_institution_config
from academic_ingest.discovery.robots import RobotsPolicy
from academic_ingest.fetching.client import FetchOutcome, SafeFetchClient
from academic_ingest.runtime import run_sync


class InspectionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: str
    outcome: str
    status_code: int | None = None
    final_url: str | None = None
    content_type: str | None = None
    content_size_bytes: int | None = Field(default=None, ge=0)
    etag: str | None = None
    last_modified: str | None = None
    warnings: list[str] = Field(default_factory=list)


async def _inspect_live(
    urls: Sequence[str],
    *,
    contact_email: str,
    config_path: Path | str,
) -> list[InspectionResult]:
    config = load_institution_config(config_path)
    results: list[InspectionResult] = []
    robots_cache: dict[str, RobotsPolicy | None] = {}
    async with SafeFetchClient(
        config,
        contact_email=contact_email,
        network_enabled=True,
    ) as client:
        for url in urls:
            if not config.is_allowed_url(url):
                results.append(
                    InspectionResult(
                        url=url,
                        outcome="skipped",
                        warnings=["source_outside_configured_scope"],
                    )
                )
                continue
            parsed = urlsplit(url)
            origin = f"{parsed.scheme}://{parsed.netloc}"
            if origin not in robots_cache:
                robots_result = await client.fetch(f"{origin}/robots.txt", uuid4())
                if robots_result.outcome == FetchOutcome.FETCHED and robots_result.content:
                    robots_cache[origin] = RobotsPolicy.from_text(
                        f"{origin}/robots.txt",
                        robots_result.content.decode("utf-8", errors="replace"),
                        user_agent=config.request_policy.build_user_agent(contact_email),
                    )
                else:
                    robots_cache[origin] = None
            robots = robots_cache[origin]
            if robots is None:
                results.append(
                    InspectionResult(
                        url=url,
                        outcome="skipped",
                        warnings=["robots_unavailable_fail_closed"],
                    )
                )
                continue
            decision = robots.evaluate(url)
            if not decision.allowed:
                results.append(
                    InspectionResult(
                        url=url,
                        outcome="skipped",
                        warnings=["robots_disallowed"],
                    )
                )
                continue
            try:
                fetched = await client.fetch(url, uuid4())
            except Exception as error:
                results.append(
                    InspectionResult(
                        url=url,
                        outcome="failed",
                        warnings=[f"{type(error).__name__}: {error}"],
                    )
                )
                continue
            results.append(
                InspectionResult(
                    url=url,
                    outcome=fetched.outcome.value,
                    status_code=fetched.status_code,
                    final_url=fetched.final_url,
                    content_type=fetched.content_type,
                    content_size_bytes=(
                        len(fetched.content) if fetched.content is not None else None
                    ),
                    etag=fetched.etag,
                    last_modified=fetched.last_modified,
                    warnings=[fetched.skip_reason] if fetched.skip_reason else [],
                )
            )
    return results


def inspect_sources(
    urls: Sequence[str],
    allow_network: bool,
    *,
    contact_email: str | None = None,
    config_path: Path | str = "config/institutions/uw_seattle.yaml",
) -> list[InspectionResult]:
    if not allow_network:
        return [
            InspectionResult(url=url, outcome="skipped", warnings=["network_disabled"])
            for url in urls
        ]
    resolved_contact = (contact_email or os.getenv("ACADEMIC_INGEST_CONTACT_EMAIL", "")).strip()
    if not resolved_contact:
        raise ValueError("ACADEMIC_INGEST_CONTACT_EMAIL is required for live inspection")
    return run_sync(_inspect_live(urls, contact_email=resolved_contact, config_path=config_path))


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect bounded official UW Seattle sources")
    parser.add_argument("urls", nargs="*", help="Official UW URLs; defaults to configured seeds")
    parser.add_argument("--allow-network", action="store_true")
    parser.add_argument(
        "--config",
        default="config/institutions/uw_seattle.yaml",
        help="Institution configuration path",
    )
    args = parser.parse_args()
    config = load_institution_config(args.config)
    urls = args.urls or config.seed_urls
    results = inspect_sources(
        urls,
        allow_network=args.allow_network,
        config_path=args.config,
    )
    print(json.dumps([item.model_dump(mode="json") for item in results], indent=2))
    return 0 if all(item.outcome != "failed" for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
