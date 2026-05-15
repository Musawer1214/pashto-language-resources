"""Promote valid candidate resources into the verified catalog.

Usage:
    python scripts/promote_candidates.py
    python scripts/promote_candidates.py --max-promotions 10
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any

try:
    from scripts.validate_resource_catalog import validate_resource
except ModuleNotFoundError:
    from validate_resource_catalog import validate_resource

try:
    from scripts.review_existing_resources import probe_resource_url, resource_probe_rejection_reasons
except ModuleNotFoundError:
    from review_existing_resources import probe_resource_url, resource_probe_rejection_reasons

try:
    from scripts.resource_quality import PLACEHOLDER_PRIMARY_USE, assess_candidate_confidence
except ModuleNotFoundError:
    from resource_quality import PLACEHOLDER_PRIMARY_USE, assess_candidate_confidence


AUTO_PROMOTED_PRIMARY_USE = "Cataloged Pashto resource discovered through the automated intake pipeline."
def _canonical_url(value: str) -> str:
    return value.rstrip("/")


def _normalized_tasks(value: Any) -> list[str]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str) and item.strip()]
    return []


def _prepare_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    promoted = dict(candidate)
    promoted["status"] = "verified"
    promoted["tasks"] = _normalized_tasks(promoted.get("tasks"))
    if isinstance(promoted.get("tags"), list):
        promoted["tags"] = [
            tag for tag in promoted["tags"] if isinstance(tag, str) and tag.strip() and tag != "candidate"
        ]

    primary_use = str(promoted.get("primary_use", "")).strip()
    if primary_use == PLACEHOLDER_PRIMARY_USE:
        promoted["primary_use"] = AUTO_PROMOTED_PRIMARY_USE
    return promoted


def _candidate_url_unavailable(candidate: dict[str, Any], timeout: float) -> bool:
    url = str(candidate.get("url", "")).strip()
    if not url:
        return True
    probe = probe_resource_url(url, timeout)
    return bool(resource_probe_rejection_reasons(candidate, probe))


def promote_candidates(
    catalog: dict[str, Any],
    pending_payload: dict[str, Any],
    *,
    max_promotions: int | None = None,
    allow_review_confidence: bool = False,
    verify_urls: bool = False,
    url_timeout: float = 10.0,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    resources = catalog.get("resources")
    if not isinstance(resources, list):
        raise ValueError("catalog.resources must be a list")

    candidates = pending_payload.get("candidates", [])
    if not isinstance(candidates, list):
        raise ValueError("pending candidates payload must include a 'candidates' list")

    seen_ids = {
        resource.get("id")
        for resource in resources
        if isinstance(resource, dict) and isinstance(resource.get("id"), str)
    }
    seen_urls = {
        _canonical_url(resource.get("url", ""))
        for resource in resources
        if isinstance(resource, dict) and isinstance(resource.get("url"), str)
    }

    promoted: list[dict[str, Any]] = []
    stats = {
        "total": len(candidates),
        "promoted": 0,
        "duplicate": 0,
        "invalid": 0,
        "unavailable": 0,
        "needs_review": 0,
    }

    for candidate in candidates:
        if max_promotions is not None and len(promoted) >= max_promotions:
            break
        if not isinstance(candidate, dict):
            stats["invalid"] += 1
            continue

        resource = _prepare_candidate(candidate)
        rid = resource.get("id")
        url = resource.get("url")
        if not isinstance(rid, str) or not isinstance(url, str):
            stats["invalid"] += 1
            continue

        canonical_url = _canonical_url(url)
        if rid in seen_ids or canonical_url in seen_urls:
            stats["duplicate"] += 1
            continue

        if verify_urls and _candidate_url_unavailable(candidate, url_timeout):
            stats["unavailable"] += 1
            continue

        confidence, _reasons = assess_candidate_confidence(candidate)
        if confidence == "low" or (confidence == "review" and not allow_review_confidence):
            stats["needs_review"] += 1
            continue

        errors = validate_resource(resource, len(resources) + len(promoted))
        if errors:
            stats["invalid"] += 1
            continue

        seen_ids.add(rid)
        seen_urls.add(canonical_url)
        promoted.append(resource)

    if promoted:
        resources.extend(promoted)
        catalog["resources"] = resources
        catalog["updated_on"] = date.today().isoformat()
    stats["promoted"] = len(promoted)
    return promoted, stats


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", default="resources/catalog/resources.json")
    parser.add_argument("--candidates", default="resources/catalog/pending_candidates.json")
    parser.add_argument("--max-promotions", type=int, default=None)
    parser.add_argument(
        "--allow-review-confidence",
        action="store_true",
        help="Also promote borderline direct-signal candidates that still need deeper maintainer enrichment.",
    )
    parser.add_argument("--skip-url-check", action="store_true")
    parser.add_argument("--url-timeout", type=float, default=10.0)
    args = parser.parse_args()

    catalog_path = Path(args.catalog)
    candidates_path = Path(args.candidates)

    if not catalog_path.exists():
        print(f"Missing catalog file: {catalog_path}")
        return 1
    if not candidates_path.exists():
        print(f"Missing candidates file: {candidates_path}")
        return 1

    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        pending_payload = json.loads(candidates_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON input: {exc}")
        return 1

    promoted, stats = promote_candidates(
        catalog,
        pending_payload,
        max_promotions=args.max_promotions,
        allow_review_confidence=args.allow_review_confidence,
        verify_urls=not args.skip_url_check,
        url_timeout=args.url_timeout,
    )
    if not promoted:
        print(
            "Promotion complete: no new verified resources "
            f"(duplicates={stats['duplicate']}, invalid={stats['invalid']}, "
            f"unavailable={stats['unavailable']}, needs_review={stats['needs_review']})"
        )
        return 0

    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "Promotion complete: "
        "promoted="
        f"{stats['promoted']} duplicate={stats['duplicate']} invalid={stats['invalid']} "
        f"unavailable={stats['unavailable']} needs_review={stats['needs_review']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
