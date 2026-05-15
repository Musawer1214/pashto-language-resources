"""Review existing catalog entries and remove only with strong evidence.

This script enforces a conservative pre-sync audit:
- Keep resources that are reachable and Pashto-relevant.
- Remove only when there is a strong reason (for example hard 404/410, duplicate ID/URL,
  or no Pashto signal in metadata and live page content).
- Persist removal reasons in a log for maintainer review.

Usage:
    python scripts/review_existing_resources.py
    python scripts/review_existing_resources.py --timeout 15
    python scripts/review_existing_resources.py --dry-run
"""

from __future__ import annotations

import argparse
import concurrent.futures as futures
import json
import re
import socket
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:
    from scripts.validate_resource_catalog import validate_resource
except ModuleNotFoundError:
    from validate_resource_catalog import validate_resource


USER_AGENT = "pashto-resource-review/1.0"
MAX_BODY_BYTES = 120_000
HARD_REMOVE_HTTP_CODES = {404, 410, 451}
STRONG_UNAVAILABLE_PATTERNS = (
    "repository not found",
    "model not found",
    "dataset not found",
    "space not found",
    "project not found",
    "record not found",
    "resource not found",
    "doi not found",
    "this item does not exist",
    "this resource does not exist",
    "this dataset does not exist",
    "this model does not exist",
    "this repository does not exist",
    "this space does not exist",
    "this project does not exist",
    "this item has been deleted",
    "this resource has been deleted",
    "this dataset has been deleted",
    "this model has been deleted",
    "this repository has been deleted",
    "this space has been deleted",
    "this project has been deleted",
    "this record has been deleted",
    "this page has been removed",
    "this resource has been removed",
    "has been withdrawn",
    "no longer available",
    "is no longer available",
)
WEAK_UNAVAILABLE_PATTERNS = (
    "page not found",
    "not found",
    "we couldn't find",
)
CONTENTLESS_RESOURCE_PATTERNS = (
    "this repository is empty",
    "repository is empty",
    "empty repository",
    "this project is empty",
    "project is empty",
    "empty project",
    "this dataset is empty",
    "dataset is empty",
    "empty dataset",
    "this model repository is empty",
    "model repository is empty",
    "no files have been uploaded",
    "there are no files",
    "no files found",
    "no reusable resource content",
    "zero tracked files",
    "only a license file",
)
AUTOMATED_PRIMARY_USE = "Automated discovery entry for Pashto resource tracking."
PASHTO_WORD_RE = re.compile(r"(?<![A-Za-z0-9])(pashto|pukhto|pushto|pakhto)(?![A-Za-z0-9])", re.IGNORECASE)
PASHTO_CODE_RE = re.compile(r"\b(ps(_af)?|pus|pbt[_-]?arab)\b", re.IGNORECASE)
PASHTO_SCRIPT_MARKERS = ("پښتو", "پشتو")
GITHUB_PROFILE_PATTERNS = (
    "config files for my github profile",
    "special repository because its `readme.md`",
    "special repository because its readme.md",
    "appears on your github profile",
)
GITHUB_EMPTY_PATTERNS = (
    "this repository is empty",
    "repository is empty",
)


@dataclass
class UrlProbe:
    status_code: int | None = None
    final_url: str | None = None
    content_sample: str = ""
    hard_missing: bool = False
    uncertain_error: str | None = None


def _contains_pashto_marker(value: str) -> bool:
    text = (value or "").strip()
    if not text:
        return False
    if PASHTO_WORD_RE.search(text):
        return True
    if PASHTO_CODE_RE.search(text):
        return True
    return any(marker in text for marker in PASHTO_SCRIPT_MARKERS)


def _resource_metadata_has_pashto_signal(resource: dict[str, Any]) -> bool:
    values: list[str] = []
    for key in ("title", "url", "summary", "primary_use"):
        item = resource.get(key)
        if isinstance(item, str):
            values.append(item)

    tags = resource.get("tags")
    if isinstance(tags, list):
        values.extend(tag for tag in tags if isinstance(tag, str))

    evidence = resource.get("pashto_evidence")
    if isinstance(evidence, dict):
        for key in ("evidence_text", "evidence_url"):
            item = evidence.get(key)
            if isinstance(item, str):
                values.append(item)
        markers = evidence.get("markers")
        if isinstance(markers, list):
            values.extend(marker for marker in markers if isinstance(marker, str))

    return any(_contains_pashto_marker(value) for value in values)


def _resource_has_direct_pashto_signal(resource: dict[str, Any]) -> bool:
    values: list[str] = []
    for key in ("title", "url"):
        item = resource.get(key)
        if isinstance(item, str):
            values.append(item)

    evidence = resource.get("pashto_evidence")
    if isinstance(evidence, dict):
        evidence_url = evidence.get("evidence_url")
        if isinstance(evidence_url, str):
            values.append(evidence_url)
        markers = evidence.get("markers")
        if isinstance(markers, list):
            values.extend(marker for marker in markers if isinstance(marker, str))

    return any(_contains_pashto_marker(value) for value in values)


def _is_automated_candidate_like(resource: dict[str, Any]) -> bool:
    rid = resource.get("id")
    primary_use = resource.get("primary_use")
    status = resource.get("status")
    tags = resource.get("tags")
    return (isinstance(rid, str) and rid.startswith("candidate-")) or (
        isinstance(primary_use, str) and primary_use.strip() == AUTOMATED_PRIMARY_USE
    ) or (
        isinstance(status, str) and status.strip() == "candidate"
    ) or (
        isinstance(tags, list) and "candidate" in tags
    )


def _is_github_candidate_like(resource: dict[str, Any]) -> bool:
    source = str(resource.get("source", "")).strip().casefold()
    url = str(resource.get("url", "")).strip().casefold()
    return _is_automated_candidate_like(resource) and (source == "github" or "github.com/" in url)


def _github_profile_marker(resource: dict[str, Any], content_sample: str) -> bool:
    values = [
        str(resource.get("title", "")),
        str(resource.get("summary", "")),
        str(resource.get("primary_use", "")),
        content_sample,
    ]
    text = "\n".join(values).casefold()
    return any(pattern in text for pattern in GITHUB_PROFILE_PATTERNS)


def _github_empty_marker(content_sample: str) -> bool:
    text = content_sample.casefold()
    return any(pattern in text for pattern in GITHUB_EMPTY_PATTERNS)


def _content_unavailable_marker(content_sample: str, *, page_pashto: bool) -> bool:
    text = content_sample.casefold()
    if any(pattern in text for pattern in STRONG_UNAVAILABLE_PATTERNS):
        return True
    return not page_pashto and any(pattern in text for pattern in WEAK_UNAVAILABLE_PATTERNS)


def _contentless_resource_marker(content_sample: str) -> bool:
    text = content_sample.casefold()
    return any(pattern in text for pattern in CONTENTLESS_RESOURCE_PATTERNS)


def resource_probe_rejection_reasons(resource: dict[str, Any], probe: UrlProbe) -> list[str]:
    """Return strong removal/promotion-block reasons from a URL probe.

    These checks intentionally focus on permanent conditions that are meaningful
    for every source: hard-missing HTTP status, deleted/unavailable pages, and
    empty/contentless automated candidates. Transient network failures remain
    warnings handled by the caller.
    """

    reasons: list[str] = []
    if probe.hard_missing:
        status_code = probe.status_code if probe.status_code is not None else "unknown"
        reasons.append(f"URL returned hard-missing HTTP status {status_code}.")

    page_pashto = _contains_pashto_marker(probe.content_sample)
    if probe.content_sample and _content_unavailable_marker(probe.content_sample, page_pashto=page_pashto):
        reasons.append("Live page content indicates resource is unavailable.")

    if _is_automated_candidate_like(resource) and _contentless_resource_marker(probe.content_sample):
        reasons.append("Automated candidate live page appears empty or contentless.")

    if _is_github_candidate_like(resource):
        if _github_empty_marker(probe.content_sample):
            reasons.append("GitHub repository is empty.")
        if _github_profile_marker(resource, probe.content_sample):
            reasons.append("GitHub profile/config repository, not a reusable Pashto resource.")

    return reasons


def _canonical_url(value: str) -> str:
    return value.rstrip("/")


def _request_url(url: str, method: str, timeout: float) -> UrlProbe:
    request = Request(url, method=method, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=timeout) as response:
            status = getattr(response, "status", 200)
            final_url = response.geturl()
            sample = ""
            if method == "GET":
                payload = response.read(MAX_BODY_BYTES)
                sample = payload.decode("utf-8", errors="replace")
            return UrlProbe(status_code=status, final_url=final_url, content_sample=sample)
    except HTTPError as exc:
        if method == "GET":
            try:
                payload = exc.read(MAX_BODY_BYTES)
                sample = payload.decode("utf-8", errors="replace")
            except Exception:  # noqa: BLE001
                sample = ""
        else:
            sample = ""
        return UrlProbe(
            status_code=exc.code,
            final_url=exc.geturl(),
            content_sample=sample,
            hard_missing=exc.code in HARD_REMOVE_HTTP_CODES,
        )
    except (URLError, TimeoutError, socket.timeout) as exc:
        return UrlProbe(uncertain_error=str(exc))


def probe_resource_url(url: str, timeout: float) -> UrlProbe:
    head = _request_url(url, "HEAD", timeout)
    if head.uncertain_error:
        return head
    if head.status_code in HARD_REMOVE_HTTP_CODES:
        head.hard_missing = True
        return head
    if head.status_code in {403, 405, 429} or head.status_code is None:
        get_result = _request_url(url, "GET", timeout)
        if get_result.status_code in HARD_REMOVE_HTTP_CODES:
            get_result.hard_missing = True
        return get_result
    if head.status_code and 200 <= head.status_code < 400:
        get_result = _request_url(url, "GET", timeout)
        if get_result.uncertain_error:
            return head
        return get_result
    return head


def review_resources(
    catalog: dict[str, Any],
    *,
    timeout: float = 12.0,
    enforce_pashto_relevance: bool = False,
    max_workers: int = 12,
    probe_fn: Any = probe_resource_url,
) -> tuple[dict[str, Any], dict[str, Any]]:
    resources = catalog.get("resources")
    if not isinstance(resources, list):
        raise ValueError("catalog.resources must be a list")

    kept: list[dict[str, Any]] = []
    removals: list[dict[str, Any]] = []
    warnings: list[str] = []
    seen_ids: dict[str, str] = {}
    seen_urls: dict[tuple[str, str], str] = {}

    probe_results: dict[str, UrlProbe] = {}
    candidate_urls = sorted(
        {
            resource.get("url", "").strip()
            for resource in resources
            if isinstance(resource, dict) and isinstance(resource.get("url"), str) and resource.get("url", "").strip()
        }
    )
    if candidate_urls:
        worker_count = max(1, min(max_workers, len(candidate_urls)))
        with futures.ThreadPoolExecutor(max_workers=worker_count) as executor:
            future_map = {executor.submit(probe_fn, url, timeout): url for url in candidate_urls}
            for future in futures.as_completed(future_map):
                url = future_map[future]
                try:
                    probe_results[url] = future.result()
                except Exception as exc:  # noqa: BLE001
                    probe_results[url] = UrlProbe(uncertain_error=str(exc))

    for index, resource in enumerate(resources):
        if not isinstance(resource, dict):
            removals.append(
                {
                    "id": f"resource-{index}",
                    "title": "",
                    "url": "",
                    "reasons": ["Entry is not a JSON object."],
                    "evidence": {},
                }
            )
            continue

        rid = resource.get("id", "")
        title = resource.get("title", "")
        url = resource.get("url", "")
        category = resource.get("category", "")
        reasons: list[str] = []

        if not isinstance(rid, str) or not rid.strip():
            reasons.append("Missing or invalid resource id.")
        if not isinstance(url, str) or not url.strip():
            reasons.append("Missing or invalid resource URL.")

        if isinstance(rid, str) and rid:
            previous = seen_ids.get(rid)
            if previous:
                reasons.append(f"Duplicate resource id; already used by '{previous}'.")

        canonical_url = _canonical_url(url) if isinstance(url, str) else ""
        normalized_category = str(category).strip().casefold() if isinstance(category, str) else ""
        if canonical_url:
            previous = seen_urls.get((normalized_category, canonical_url))
            if previous:
                reasons.append(
                    "Duplicate canonical URL in same category; "
                    f"already used by '{previous}'."
                )

        validation_errors = validate_resource(resource, index)
        if any(".url must be a valid http/https URL" in error for error in validation_errors):
            reasons.append("Resource URL failed schema validation.")

        probe = UrlProbe()
        if isinstance(url, str) and url.strip():
            probe = probe_results.get(url, UrlProbe())
            if probe.uncertain_error:
                warnings.append(f"{rid or f'resource-{index}'} URL probe inconclusive: {probe.uncertain_error}")
            else:
                reasons.extend(resource_probe_rejection_reasons(resource, probe))

        metadata_pashto = _resource_metadata_has_pashto_signal(resource)
        direct_pashto = _resource_has_direct_pashto_signal(resource)
        page_pashto = _contains_pashto_marker(probe.content_sample)
        signal_origin = "direct" if direct_pashto else "metadata" if metadata_pashto else "none"

        if enforce_pashto_relevance and not metadata_pashto and not page_pashto:
            reasons.append("No Pashto signal found in metadata or live page content.")

        if enforce_pashto_relevance and _is_automated_candidate_like(resource) and not direct_pashto and not page_pashto:
            reasons.append("Automated candidate lacks direct Pashto signal and appears low-confidence.")

        if reasons:
            removals.append(
                {
                    "id": rid,
                    "title": title,
                    "url": url,
                    "reasons": reasons,
                    "evidence": {
                        "status_code": probe.status_code,
                        "final_url": probe.final_url,
                        "metadata_pashto": metadata_pashto,
                        "direct_pashto": direct_pashto,
                        "page_pashto": page_pashto,
                        "signal_origin": signal_origin,
                    },
                }
            )
            continue

        kept.append(resource)
        if isinstance(rid, str) and rid:
            seen_ids[rid] = title if isinstance(title, str) else rid
        if canonical_url:
            seen_urls[(normalized_category, canonical_url)] = (
                title if isinstance(title, str) else canonical_url
            )

    updated_catalog = dict(catalog)
    if len(kept) != len(resources):
        updated_catalog["resources"] = kept
        updated_catalog["updated_on"] = date.today().isoformat()

    report = {
        "checked": len(resources),
        "kept": len(kept),
        "removed": len(removals),
        "removals": removals,
        "warnings": warnings,
    }
    return updated_catalog, report


def update_removal_log(log_path: Path, removals: list[dict[str, Any]]) -> None:
    payload: dict[str, Any]
    if log_path.exists():
        try:
            payload = json.loads(log_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = {"updated_on": date.today().isoformat(), "entries": []}
    else:
        payload = {"updated_on": date.today().isoformat(), "entries": []}

    entries = payload.get("entries")
    if not isinstance(entries, list):
        entries = []

    removed_on = datetime.now(timezone.utc).isoformat()
    for item in removals:
        entries.append(
            {
                "removed_on": removed_on,
                "id": item.get("id", ""),
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "reasons": item.get("reasons", []),
                "evidence": item.get("evidence", {}),
            }
        )

    payload["updated_on"] = date.today().isoformat()
    payload["entries"] = entries
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", default="resources/catalog/resources.json")
    parser.add_argument("--timeout", type=float, default=12.0)
    parser.add_argument("--max-workers", type=int, default=12)
    parser.add_argument("--removal-log", default="resources/catalog/removal_log.json")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--enforce-pashto-relevance",
        action="store_true",
        help="Also remove entries that have no Pashto signal in metadata or live page content.",
    )
    args = parser.parse_args()

    catalog_path = Path(args.catalog)
    removal_log_path = Path(args.removal_log)
    if not catalog_path.exists():
        print(f"Missing catalog file: {catalog_path}")
        return 1

    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Invalid catalog JSON: {exc}")
        return 1

    updated_catalog, report = review_resources(
        catalog,
        timeout=args.timeout,
        enforce_pashto_relevance=args.enforce_pashto_relevance,
        max_workers=args.max_workers,
        probe_fn=probe_resource_url,
    )

    print(
        "Resource review complete: "
        f"checked={report['checked']} kept={report['kept']} removed={report['removed']} "
        f"warnings={len(report['warnings'])}"
    )

    if report["warnings"]:
        for warning in report["warnings"]:
            print(f"[warn] {warning}")

    if report["removed"]:
        for item in report["removals"]:
            rid = item.get("id", "<unknown>")
            reasons = item.get("reasons", [])
            print(f"[remove] {rid}")
            for reason in reasons:
                print(f"  - {reason}")

        if not args.dry_run:
            catalog_path.write_text(json.dumps(updated_catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            update_removal_log(removal_log_path, report["removals"])
    elif not args.dry_run and updated_catalog != catalog:
        # Defensive branch for any non-removal edits.
        catalog_path.write_text(json.dumps(updated_catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
