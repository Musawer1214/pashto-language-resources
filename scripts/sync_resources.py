"""Discover new Pashto-related resource candidates from public endpoints.

This script does not auto-merge into the main catalog. It writes candidates to
`resources/catalog/pending_candidates.json` for maintainer review.

Usage:
    python scripts/sync_resources.py
    python scripts/sync_resources.py --limit 20 --output resources/catalog/pending_candidates.json
"""

from __future__ import annotations

import argparse
import json
import re
import socket
import ssl
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from http.client import IncompleteRead
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError


USER_AGENT = "pashto-resource-sync/1.0"
MAX_FETCH_RETRIES = 4
RETRYABLE_HTTP_CODES = {429, 500, 502, 503, 504}
HARD_REMOVE_HTTP_CODES = {404, 410, 451}
BLOCKING_REMOVAL_REASON_MARKERS = (
    "hard-missing http status",
    "unavailable",
    "deleted",
    "removed",
    "empty",
    "contentless",
    "zero tracked files",
    "only a license file",
    "no reusable resource content",
    "not a reusable",
    "not a pashto",
    "no pashto signal",
    "lacks direct pashto signal",
    "low-confidence",
    "profile/config",
    "personal",
    "generic web page",
)
PASHTO_QUERY_TERMS = ["pashto", "pukhto", "pushto", "pakhto"]
PASHTO_TEXT_MARKERS = ("pashto", "pukhto", "pushto", "pakhto")
PASHTO_SCRIPT_MARKERS = ("پښتو", "پشتو")
PASHTO_WORD_RE = re.compile(
    r"(?<![A-Za-z0-9])(pashto|pukhto|pushto|pakhto)(?![A-Za-z0-9])",
    re.IGNORECASE,
)
PASHTO_CAMEL_RE = re.compile(
    r"(?<![A-Za-z0-9])(pashto|pukhto|pakhto)(?=[A-Z])",
    re.IGNORECASE,
)
PASHTO_CODE_RE = re.compile(r"\b(ps(_af)?|pus|pbt[_-]?arab)\b", re.IGNORECASE)
LOW_SIGNAL_RE = re.compile(r"(^|[-_/ ])(test|tmp|trial|scratch)([-_/ ]|$)", re.IGNORECASE)


def _slug(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value[:80] if value else "resource"


def _canonical_url(value: str) -> str:
    return value.rstrip("/")


def _contains_pashto_marker(value: str) -> bool:
    text = (value or "").strip()
    if not text:
        return False
    if PASHTO_WORD_RE.search(text):
        return True
    if PASHTO_CAMEL_RE.search(text):
        return True
    if any(marker in text for marker in PASHTO_SCRIPT_MARKERS):
        return True
    lowered = text.casefold()
    return bool(PASHTO_CODE_RE.search(lowered))


def _is_pashto_centric(*values: str) -> bool:
    return any(_contains_pashto_marker(value) for value in values)


def _is_low_signal_name(value: str) -> bool:
    return bool(LOW_SIGNAL_RE.search(value or ""))


def _strip_html(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value or "")
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _classify_repo_category(name_blob: str) -> str:
    lowered = (name_blob or "").casefold()
    code_tokens = ("toolkit", "library", "nlp", "asr", "tts", "ocr", "api", "code", "cli", "sdk")
    if any(token in lowered for token in code_tokens):
        return "code"
    return "project"


def _parse_retry_after_seconds(retry_after: str | None) -> float | None:
    if not retry_after:
        return None

    retry_after = retry_after.strip()
    if not retry_after:
        return None

    if retry_after.isdigit():
        return float(retry_after)

    try:
        retry_at = parsedate_to_datetime(retry_after)
    except (TypeError, ValueError):
        return None

    now = datetime.now(timezone.utc)
    if retry_at.tzinfo is None:
        retry_at = retry_at.replace(tzinfo=timezone.utc)
    return max(0.0, (retry_at - now).total_seconds())


def _is_ssl_cert_error(exc: BaseException) -> bool:
    if isinstance(exc, ssl.SSLCertVerificationError):
        return True
    if isinstance(exc, URLError):
        reason = exc.reason
        if isinstance(reason, ssl.SSLCertVerificationError):
            return True
    return "CERTIFICATE_VERIFY_FAILED" in str(exc)


def _retryable_network_error(exc: BaseException) -> bool:
    if _is_ssl_cert_error(exc):
        return False
    if isinstance(exc, (TimeoutError, socket.timeout, IncompleteRead, ConnectionResetError)):
        return True
    if isinstance(exc, URLError):
        reason = exc.reason
        if isinstance(reason, (TimeoutError, socket.timeout, IncompleteRead, ConnectionResetError)):
            return True
        return True
    return False


def _retry_delay(attempt: int, retry_after: str | None = None) -> float:
    parsed = _parse_retry_after_seconds(retry_after)
    if parsed is not None:
        return min(max(parsed, 0.0), 60.0)
    return min(2 ** (attempt - 1), 30.0)


def _fetch_bytes(
    url: str,
    *,
    timeout: float = 20.0,
    ssl_context: ssl.SSLContext | None = None,
    source_name: str = "remote",
) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last_exc: BaseException | None = None

    for attempt in range(1, MAX_FETCH_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=ssl_context) as response:
                return response.read()
        except HTTPError as exc:
            last_exc = exc
            if exc.code in RETRYABLE_HTTP_CODES and attempt < MAX_FETCH_RETRIES:
                delay = _retry_delay(attempt, exc.headers.get("Retry-After"))
                print(
                    f"[retry] {source_name} HTTP {exc.code} from {url}; "
                    f"retrying in {delay:.1f}s ({attempt}/{MAX_FETCH_RETRIES})"
                )
                time.sleep(delay)
                continue
            raise
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if _retryable_network_error(exc) and attempt < MAX_FETCH_RETRIES:
                delay = _retry_delay(attempt)
                print(
                    f"[retry] {source_name} network error from {url}: {exc}; "
                    f"retrying in {delay:.1f}s ({attempt}/{MAX_FETCH_RETRIES})"
                )
                time.sleep(delay)
                continue
            raise

    if last_exc is not None:
        raise RuntimeError(f"{source_name} fetch failed after retries: {last_exc}") from last_exc
    raise RuntimeError(f"{source_name} fetch failed unexpectedly for {url}")


def _fetch_json(
    url: str,
    *,
    timeout: float = 20.0,
    ssl_context: ssl.SSLContext | None = None,
    source_name: str = "remote",
) -> Any:
    payload = _fetch_bytes(
        url,
        timeout=timeout,
        ssl_context=ssl_context,
        source_name=source_name,
    )
    return json.loads(payload.decode("utf-8"))


def _fetch_text(
    url: str,
    *,
    timeout: float = 20.0,
    ssl_context: ssl.SSLContext | None = None,
    source_name: str = "remote",
) -> str:
    payload = _fetch_bytes(
        url,
        timeout=timeout,
        ssl_context=ssl_context,
        source_name=source_name,
    )
    return payload.decode("utf-8", errors="replace")


def _candidate(
    *,
    rid: str,
    title: str,
    url: str,
    category: str,
    source: str,
    summary: str,
    evidence_text: str,
    evidence_url: str,
    markers: list[str],
    tags: list[str],
) -> dict[str, Any]:
    return {
        "id": rid,
        "title": title.strip(),
        "url": url.strip(),
        "category": category,
        "source": source,
        "status": "candidate",
        "summary": summary.strip(),
        "primary_use": "Needs maintainer review before promotion to verified catalog.",
        "tasks": [],
        "pashto_evidence": {
            "evidence_text": evidence_text.strip(),
            "evidence_url": evidence_url.strip(),
            "markers": markers,
        },
        "tags": tags,
    }


def fetch_huggingface(kind: str, limit: int) -> list[dict[str, Any]]:
    if kind not in {"datasets", "models"}:
        return []

    combined: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for term in PASHTO_QUERY_TERMS:
        query = urllib.parse.urlencode({"search": term, "limit": str(limit)})
        url = f"https://huggingface.co/api/{kind}?{query}"
        try:
            payload = _fetch_json(url, source_name=f"huggingface-{kind}")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{term}: {exc}")
            continue
        for item in payload:
            repo_id = item.get("id") or item.get("modelId")
            if not repo_id:
                continue
            combined[repo_id] = item

    if not combined and errors:
        raise RuntimeError("; ".join(errors))

    category = "dataset" if kind == "datasets" else "model"
    out: list[dict[str, Any]] = []
    for item in combined.values():
        repo_id = item.get("id") or item.get("modelId")
        if not repo_id:
            continue
        if not _is_pashto_centric(repo_id):
            continue
        if _is_low_signal_name(repo_id):
            continue
        repo_url = f"https://huggingface.co/{'datasets/' if kind == 'datasets' else ''}{repo_id}"
        rid = f"candidate-hf-{kind[:-1]}-{_slug(repo_id)}"
        out.append(
            _candidate(
                rid=rid,
                title=repo_id,
                url=repo_url,
                category=category,
                source="huggingface",
                summary=f"Candidate {category} returned from Hugging Face search for Pashto.",
                evidence_text="Matched by Pashto keyword in Hugging Face search results.",
                evidence_url=repo_url,
                markers=["pashto"],
                tags=["pashto", "candidate", category],
            )
        )
        if len(out) >= limit:
            break
    return out


def fetch_huggingface_spaces(limit: int) -> list[dict[str, Any]]:
    combined: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for term in PASHTO_QUERY_TERMS:
        query = urllib.parse.urlencode({"search": term, "limit": str(limit)})
        url = f"https://huggingface.co/api/spaces?{query}"
        try:
            payload = _fetch_json(url, source_name="huggingface-spaces")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{term}: {exc}")
            continue
        for item in payload:
            space_id = item.get("id")
            if not space_id:
                continue
            combined[space_id] = item

    if not combined and errors:
        raise RuntimeError("; ".join(errors))

    out: list[dict[str, Any]] = []
    for item in combined.values():
        space_id = item.get("id")
        if not space_id:
            continue
        if not _is_pashto_centric(space_id):
            continue
        if _is_low_signal_name(space_id):
            continue
        space_url = f"https://huggingface.co/spaces/{space_id}"
        rid = f"candidate-hf-project-{_slug(space_id)}"
        summary = "Candidate project app returned from Hugging Face Spaces Pashto search."
        out.append(
            _candidate(
                rid=rid,
                title=space_id,
                url=space_url,
                category="project",
                source="huggingface",
                summary=summary,
                evidence_text="Matched by Pashto keyword in Hugging Face Spaces search.",
                evidence_url=space_url,
                markers=["pashto"],
                tags=["pashto", "candidate", "project", "space"],
            )
        )
        if len(out) >= limit:
            break
    return out


def fetch_kaggle_datasets(limit: int) -> list[dict[str, Any]]:
    # Public Kaggle dataset listing endpoint (no auth needed for list responses).
    combined: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    errors: list[str] = []
    for term in PASHTO_QUERY_TERMS:
        query = urllib.parse.urlencode({"search": term, "page": "1"})
        url = f"https://www.kaggle.com/api/v1/datasets/list?{query}"
        try:
            payload = _fetch_json(url, source_name="kaggle-datasets")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{term}: {exc}")
            continue
        for item in payload:
            dataset_url = (item.get("urlNullable") or "").strip()
            if not dataset_url or dataset_url in seen_urls:
                continue
            seen_urls.add(dataset_url)
            combined.append(item)

    if not combined and errors:
        raise RuntimeError("; ".join(errors))

    out: list[dict[str, Any]] = []
    for item in combined:
        title = (item.get("titleNullable") or "").strip()
        dataset_url = (item.get("urlNullable") or "").strip()
        owner = (item.get("ownerRefNullable") or "").strip()
        subtitle = (item.get("subtitleNullable") or "").strip()
        if not title or not dataset_url:
            continue

        if not _is_pashto_centric(title, subtitle):
            continue
        if _is_low_signal_name(title):
            continue

        owner_prefix = f"{owner}/" if owner else ""
        rid = f"candidate-kaggle-dataset-{_slug(owner_prefix + title)}"
        out.append(
            _candidate(
                rid=rid,
                title=title,
                url=dataset_url,
                category="dataset",
                source="kaggle",
                summary=(subtitle or "Candidate Kaggle dataset returned from Pashto search.")[:240],
                evidence_text="Kaggle dataset title/subtitle includes Pashto keyword.",
                evidence_url=dataset_url,
                markers=["Pashto"],
                tags=["pashto", "candidate", "dataset", "kaggle"],
            )
        )
        if len(out) >= limit:
            break
    return out


def fetch_github_pashto_repos(limit: int) -> list[dict[str, Any]]:
    # Query by topic first for high precision, then by keyword for recall.
    query_variants = [
        "topic:pashto",
        "topic:pukhto",
        "pashto in:name,description,readme",
        "pukhto in:name,description,readme",
        "pushto in:name,description,readme",
        "pakhto in:name,description,readme",
    ]

    combined: dict[str, dict[str, Any]] = {}
    for query_text in query_variants:
        query = urllib.parse.urlencode(
            {"q": query_text, "sort": "stars", "order": "desc", "per_page": str(limit)}
        )
        url = f"https://api.github.com/search/repositories?{query}"
        payload = _fetch_json(
            url,
            timeout=30.0,
            source_name="github-repositories",
        )
        for item in payload.get("items", []):
            full_name = item.get("full_name")
            html_url = item.get("html_url")
            if not full_name or not html_url:
                continue
            combined[full_name] = item

    out: list[dict[str, Any]] = []
    for full_name, item in sorted(combined.items(), key=lambda kv: kv[1].get("stargazers_count", 0), reverse=True):
        name_blob = " ".join(
            [
                full_name or "",
                item.get("name") or "",
                item.get("description") or "",
                " ".join(item.get("topics") or []),
            ]
        )
        if not _is_pashto_centric(name_blob):
            continue
        if _is_low_signal_name(full_name):
            continue

        html_url = item["html_url"]
        topics = item.get("topics") or []
        category = _classify_repo_category(name_blob)

        rid = f"candidate-gh-{category}-{_slug(full_name)}"
        description = (item.get("description") or "").strip()
        summary = description or "Candidate Pashto-related GitHub repository."
        out.append(
            _candidate(
                rid=rid,
                title=full_name,
                url=html_url,
                category=category,
                source="github",
                summary=summary[:240] if summary else "Candidate Pashto-related GitHub repository.",
                evidence_text="Repository metadata (name/description/topics) includes Pashto markers.",
                evidence_url=html_url,
                markers=["pashto"],
                tags=["pashto", "candidate", category, "github", *(topics[:3])],
            )
        )
        if len(out) >= limit:
            break
    return out


def fetch_gitlab_pashto_projects(limit: int) -> list[dict[str, Any]]:
    combined: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for term in PASHTO_QUERY_TERMS:
        query = urllib.parse.urlencode(
            {
                "search": term,
                "simple": "true",
                "order_by": "star_count",
                "sort": "desc",
                "per_page": str(limit),
            }
        )
        url = f"https://gitlab.com/api/v4/projects?{query}"
        try:
            payload = _fetch_json(url, timeout=30.0, source_name="gitlab-projects")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{term}: {exc}")
            continue
        for item in payload:
            full_name = (item.get("path_with_namespace") or item.get("name_with_namespace") or "").strip()
            if not full_name:
                continue
            combined[full_name] = item

    if not combined and errors:
        raise RuntimeError("; ".join(errors))

    out: list[dict[str, Any]] = []
    sorted_items = sorted(
        combined.items(),
        key=lambda kv: kv[1].get("star_count") or 0,
        reverse=True,
    )
    for full_name, item in sorted_items:
        web_url = (item.get("web_url") or "").strip()
        if not web_url:
            continue

        description = (item.get("description") or "").strip()
        topics = item.get("topics") or []
        if not isinstance(topics, list):
            topics = []
        topics = [str(topic).strip() for topic in topics if str(topic).strip()]
        name_blob = " ".join([full_name, item.get("name") or "", description, " ".join(topics)])
        if not _is_pashto_centric(name_blob):
            continue
        if _is_low_signal_name(full_name):
            continue

        category = _classify_repo_category(name_blob)
        rid = f"candidate-gitlab-{category}-{_slug(full_name)}"
        summary = description or "Candidate Pashto-related GitLab repository."
        out.append(
            _candidate(
                rid=rid,
                title=full_name,
                url=web_url,
                category=category,
                source="gitlab",
                summary=summary[:240] if summary else "Candidate Pashto-related GitLab repository.",
                evidence_text="Project metadata (name/description/topics) includes Pashto markers.",
                evidence_url=web_url,
                markers=["pashto"],
                tags=["pashto", "candidate", category, "gitlab", *(topics[:3])],
            )
        )
        if len(out) >= limit:
            break
    return out


def fetch_openalex_papers(limit: int) -> list[dict[str, Any]]:
    combined: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for term in PASHTO_QUERY_TERMS:
        query = urllib.parse.urlencode({"search": term, "per-page": str(limit)})
        url = f"https://api.openalex.org/works?{query}"
        try:
            payload = _fetch_json(url, timeout=30.0, source_name="openalex")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{term}: {exc}")
            continue
        for item in payload.get("results", []):
            work_id = (item.get("id") or "").strip()
            if not work_id:
                continue
            combined[work_id] = item

    if not combined and errors:
        raise RuntimeError("; ".join(errors))

    out: list[dict[str, Any]] = []
    for item in combined.values():
        title = (item.get("display_name") or "").strip()
        if not title:
            continue
        if not _is_pashto_centric(title):
            continue
        if _is_low_signal_name(title):
            continue

        doi = (item.get("doi") or "").strip()
        if doi and not doi.startswith("http"):
            doi = f"https://doi.org/{doi}"
        primary = item.get("primary_location") or {}
        landing = (primary.get("landing_page_url") or "").strip()
        paper_url = doi or landing or (item.get("id") or "").strip()
        if not paper_url:
            continue

        rid = f"candidate-openalex-{_slug(title)}"
        out.append(
            _candidate(
                rid=rid,
                title=title,
                url=paper_url,
                category="paper",
                source="openalex",
                summary="Candidate paper returned from OpenAlex works search for Pashto.",
                evidence_text="Matched by explicit Pashto marker in title from OpenAlex works search.",
                evidence_url=paper_url,
                markers=["pashto"],
                tags=["pashto", "candidate", "paper", "openalex"],
            )
        )
        if len(out) >= limit:
            break
    return out


def fetch_crossref_papers(limit: int) -> list[dict[str, Any]]:
    combined: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for term in PASHTO_QUERY_TERMS:
        query = urllib.parse.urlencode({"query.title": term, "rows": str(limit)})
        url = f"https://api.crossref.org/works?{query}"
        try:
            payload = _fetch_json(url, timeout=30.0, source_name="crossref")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{term}: {exc}")
            continue
        for item in payload.get("message", {}).get("items", []):
            doi = (item.get("DOI") or "").strip()
            title_list = item.get("title") or []
            title = (title_list[0] if isinstance(title_list, list) and title_list else "").strip()
            key = doi or title
            if not key:
                continue
            combined[key] = item

    if not combined and errors:
        raise RuntimeError("; ".join(errors))

    out: list[dict[str, Any]] = []
    for item in combined.values():
        title_list = item.get("title") or []
        title = (title_list[0] if isinstance(title_list, list) and title_list else "").strip()
        if not title:
            continue
        if not _is_pashto_centric(title):
            continue
        if _is_low_signal_name(title):
            continue

        doi = (item.get("DOI") or "").strip()
        paper_url = (item.get("URL") or "").strip()
        if not paper_url and doi:
            paper_url = f"https://doi.org/{doi}"
        if not paper_url:
            continue

        abstract = _strip_html(item.get("abstract") or "")
        rid = f"candidate-crossref-{_slug(title)}"
        out.append(
            _candidate(
                rid=rid,
                title=title,
                url=paper_url,
                category="paper",
                source="crossref",
                summary=(abstract or "Candidate paper returned from Crossref search for Pashto.")[:240],
                evidence_text="Matched by explicit Pashto marker in title from Crossref search.",
                evidence_url=paper_url,
                markers=["pashto"],
                tags=["pashto", "candidate", "paper", "crossref"],
            )
        )
        if len(out) >= limit:
            break
    return out


def fetch_zenodo_records(limit: int) -> list[dict[str, Any]]:
    combined: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for term in PASHTO_QUERY_TERMS:
        query = urllib.parse.urlencode({"q": term, "size": str(limit), "sort": "mostrecent"})
        url = f"https://zenodo.org/api/records/?{query}"
        try:
            payload = _fetch_json(url, timeout=30.0, source_name="zenodo")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{term}: {exc}")
            continue
        for item in payload.get("hits", {}).get("hits", []):
            record_id = str(item.get("id") or "").strip()
            if not record_id:
                continue
            combined[record_id] = item

    if not combined and errors:
        raise RuntimeError("; ".join(errors))

    category_map = {
        "dataset": "dataset",
        "software": "code",
        "publication": "paper",
        "poster": "project",
        "presentation": "project",
    }

    out: list[dict[str, Any]] = []
    for item in combined.values():
        metadata = item.get("metadata") or {}
        title = (metadata.get("title") or "").strip()
        description = _strip_html(metadata.get("description") or "")
        if not title:
            continue
        if not _is_pashto_centric(title, description):
            continue
        if _is_low_signal_name(title):
            continue

        links = item.get("links") or {}
        record_url = (links.get("self_html") or links.get("doi") or "").strip()
        if not record_url:
            doi = (metadata.get("doi") or "").strip()
            if doi:
                record_url = f"https://doi.org/{doi}"
        if not record_url:
            continue

        rtype = (metadata.get("resource_type") or {}).get("type") or ""
        category = category_map.get(str(rtype).casefold(), "project")
        rid = f"candidate-zenodo-{category}-{_slug(title)}"
        summary = description or "Candidate resource returned from Zenodo search for Pashto."
        out.append(
            _candidate(
                rid=rid,
                title=title,
                url=record_url,
                category=category,
                source="zenodo",
                summary=summary[:240],
                evidence_text="Zenodo metadata includes Pashto markers in title or description.",
                evidence_url=record_url,
                markers=["pashto"],
                tags=["pashto", "candidate", category, "zenodo"],
            )
        )
        if len(out) >= limit:
            break
    return out


def fetch_dataverse_datasets(limit: int) -> list[dict[str, Any]]:
    combined: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    base_url = "https://dataverse.harvard.edu"
    for term in PASHTO_QUERY_TERMS:
        query = urllib.parse.urlencode(
            {
                "q": term,
                "type": "dataset",
                "per_page": str(limit),
                "start": "0",
            }
        )
        url = f"{base_url}/api/search?{query}"
        try:
            payload = _fetch_json(url, timeout=30.0, source_name="dataverse")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{term}: {exc}")
            continue
        for item in payload.get("data", {}).get("items", []):
            key = str(item.get("global_id") or item.get("identifier") or item.get("url") or "").strip()
            if not key:
                continue
            combined[key] = item

    if not combined and errors:
        raise RuntimeError("; ".join(errors))

    out: list[dict[str, Any]] = []
    for item in combined.values():
        title = (item.get("name") or "").strip()
        description = (item.get("description") or "").strip()
        if not title:
            continue
        if not _is_pashto_centric(title, description):
            continue
        if _is_low_signal_name(title):
            continue

        record_url = (item.get("url") or "").strip()
        if record_url and record_url.startswith("/"):
            record_url = f"{base_url}{record_url}"
        if not record_url:
            global_id = (item.get("global_id") or "").strip()
            if global_id:
                escaped_id = urllib.parse.quote(global_id, safe=":/")
                record_url = f"{base_url}/dataset.xhtml?persistentId={escaped_id}"
        if not record_url:
            continue

        rid = f"candidate-dataverse-dataset-{_slug(title)}"
        out.append(
            _candidate(
                rid=rid,
                title=title,
                url=record_url,
                category="dataset",
                source="dataverse",
                summary=(description or "Candidate dataset returned from Dataverse search for Pashto.")[:240],
                evidence_text="Dataverse metadata includes Pashto markers in dataset title or description.",
                evidence_url=record_url,
                markers=["pashto"],
                tags=["pashto", "candidate", "dataset", "dataverse"],
            )
        )
        if len(out) >= limit:
            break
    return out


def fetch_datacite_records(limit: int) -> list[dict[str, Any]]:
    combined: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for term in PASHTO_QUERY_TERMS:
        query = urllib.parse.urlencode(
            {
                "query": term,
                "page[size]": str(limit),
            }
        )
        url = f"https://api.datacite.org/dois?{query}"
        try:
            payload = _fetch_json(url, timeout=30.0, source_name="datacite")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{term}: {exc}")
            continue
        for item in payload.get("data", []):
            record_id = (item.get("id") or "").strip()
            if not record_id:
                continue
            combined[record_id] = item

    if not combined and errors:
        raise RuntimeError("; ".join(errors))

    dataset_types = {"dataset", "collection"}
    software_types = {"software"}
    paper_types = {"journalarticle", "conferencepaper", "preprint", "text"}

    out: list[dict[str, Any]] = []
    for item in combined.values():
        attributes = item.get("attributes") or {}
        titles = attributes.get("titles") or []
        title = ""
        if isinstance(titles, list) and titles:
            first = titles[0] or {}
            if isinstance(first, dict):
                title = (first.get("title") or "").strip()
        if not title:
            continue
        description_items = attributes.get("descriptions") or []
        descriptions: list[str] = []
        if isinstance(description_items, list):
            for block in description_items:
                if isinstance(block, dict):
                    value = (block.get("description") or "").strip()
                    if value:
                        descriptions.append(_strip_html(value))
        description_blob = " ".join(descriptions).strip()
        if not _is_pashto_centric(title, description_blob):
            continue
        if _is_low_signal_name(title):
            continue

        doi = (attributes.get("doi") or item.get("id") or "").strip()
        record_url = (attributes.get("url") or "").strip()
        if not record_url and doi:
            record_url = f"https://doi.org/{doi}"
        if not record_url:
            continue

        general_type = str((attributes.get("types") or {}).get("resourceTypeGeneral") or "").casefold()
        if general_type in dataset_types:
            category = "dataset"
        elif general_type in software_types:
            category = "code"
        elif general_type in paper_types:
            category = "paper"
        else:
            category = "project"

        rid = f"candidate-datacite-{category}-{_slug(title)}"
        summary = description_blob or "Candidate record returned from DataCite DOI search for Pashto."
        out.append(
            _candidate(
                rid=rid,
                title=title,
                url=record_url,
                category=category,
                source="datacite",
                summary=summary[:240],
                evidence_text="DataCite metadata includes Pashto markers in title or description.",
                evidence_url=record_url,
                markers=["pashto"],
                tags=["pashto", "candidate", category, "datacite"],
            )
        )
        if len(out) >= limit:
            break
    return out


def fetch_arxiv(limit: int) -> list[dict[str, Any]]:
    roots: list[ET.Element] = []
    errors: list[str] = []
    for term in PASHTO_QUERY_TERMS:
        query = urllib.parse.urlencode(
            {"search_query": f"all:{term}", "start": "0", "max_results": str(limit)}
        )
        url = f"https://export.arxiv.org/api/query?{query}"
        try:
            xml_text = _fetch_text(url, timeout=30.0, source_name="arxiv")
        except Exception as exc:  # noqa: BLE001
            if not _is_ssl_cert_error(exc):
                errors.append(f"{term}: {exc}")
                continue
            # arXiv occasionally fails cert chain validation in some runner images.
            insecure_context = ssl._create_unverified_context()
            print("[warn] arxiv SSL verification failed; retrying with unverified TLS context")
            xml_text = _fetch_text(
                url,
                timeout=30.0,
                ssl_context=insecure_context,
                source_name="arxiv",
            )
        roots.append(ET.fromstring(xml_text))

    if not roots and errors:
        raise RuntimeError("; ".join(errors))

    ns = {"atom": "http://www.w3.org/2005/Atom"}

    seen_links: set[str] = set()
    out: list[dict[str, Any]] = []
    for root in roots:
        for entry in root.findall("atom:entry", ns):
            title = (entry.findtext("atom:title", default="", namespaces=ns) or "").strip()
            link = (entry.findtext("atom:id", default="", namespaces=ns) or "").strip()
            summary = (entry.findtext("atom:summary", default="", namespaces=ns) or "").strip()
            if not title or not link:
                continue
            if link in seen_links:
                continue
            # Strict: keep only papers with explicit Pashto markers in title.
            if not _is_pashto_centric(title):
                continue
            if _is_low_signal_name(title):
                continue

            seen_links.add(link)
            rid = f"candidate-arxiv-{_slug(title)}"
            out.append(
                _candidate(
                    rid=rid,
                    title=title,
                    url=link,
                    category="paper",
                    source="arxiv",
                    summary=summary[:240] if summary else "Candidate paper returned from arXiv query for Pashto.",
                    evidence_text="Matched by Pashto marker in paper title from arXiv query results.",
                    evidence_url=link,
                    markers=["pashto"],
                    tags=["pashto", "candidate", "paper"],
                )
            )
            if len(out) >= limit:
                return out
    return out


def fetch_semantic_scholar(limit: int) -> list[dict[str, Any]]:
    fields = "title,url,abstract,year,externalIds"
    combined: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for term in PASHTO_QUERY_TERMS:
        query = urllib.parse.urlencode(
            {"query": term, "limit": str(limit), "fields": fields}
        )
        url = f"https://api.semanticscholar.org/graph/v1/paper/search?{query}"
        try:
            payload = _fetch_json(
                url,
                timeout=30.0,
                source_name="semantic-scholar",
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{term}: {exc}")
            continue
        for item in payload.get("data", []):
            title = (item.get("title") or "").strip()
            if not title:
                continue
            combined[title] = item

    if not combined and errors:
        raise RuntimeError("; ".join(errors))

    out: list[dict[str, Any]] = []
    for item in combined.values():
        title = (item.get("title") or "").strip()
        if not title:
            continue
        # Strict: keep only papers with explicit Pashto markers in title.
        if not _is_pashto_centric(title):
            continue
        if _is_low_signal_name(title):
            continue
        paper_url = (item.get("url") or "").strip()
        if not paper_url:
            ext = item.get("externalIds") or {}
            arxiv_id = ext.get("ArXiv")
            if arxiv_id:
                paper_url = f"https://arxiv.org/abs/{arxiv_id}"
        if not paper_url:
            continue

        summary = (item.get("abstract") or "").strip()
        rid = f"candidate-s2-{_slug(title)}"
        out.append(
            _candidate(
                rid=rid,
                title=title,
                url=paper_url,
                category="paper",
                source="other",
                summary=summary[:240] if summary else "Candidate paper returned from Semantic Scholar search for Pashto.",
                evidence_text="Matched by explicit Pashto marker in paper title from Semantic Scholar search.",
                evidence_url=paper_url,
                markers=["pashto"],
                tags=["pashto", "candidate", "paper"],
            )
        )
        if len(out) >= limit:
            break
    return out


def _dedupe_candidates(
    candidates: list[dict[str, Any]],
    existing_ids: set[str],
    existing_urls: set[str],
) -> list[dict[str, Any]]:
    unique: list[dict[str, Any]] = []
    seen_ids = set(existing_ids)
    seen_urls = set(existing_urls)

    for item in candidates:
        rid = item["id"]
        url = _canonical_url(item["url"])
        if rid in seen_ids or url in seen_urls:
            continue
        seen_ids.add(rid)
        seen_urls.add(url)
        unique.append(item)
    return unique


def _load_prior_hard_removals(path: Path) -> tuple[set[str], set[str], dict[str, dict[str, Any]]]:
    if not path.exists():
        return set(), set(), {}

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return set(), set(), {}

    entries = payload.get("entries", [])
    if not isinstance(entries, list):
        return set(), set(), {}

    blocked_ids: set[str] = set()
    blocked_urls: set[str] = set()
    lookup: dict[str, dict[str, Any]] = {}

    for entry in entries:
        if not isinstance(entry, dict):
            continue
        reasons = entry.get("reasons", [])
        evidence = entry.get("evidence", {})
        status_code = evidence.get("status_code") if isinstance(evidence, dict) else None
        hard_missing = status_code in HARD_REMOVE_HTTP_CODES
        if not hard_missing and isinstance(reasons, list):
            hard_missing = any("hard-missing http status" in str(reason).casefold() for reason in reasons)
        blocking_removal = hard_missing
        if not blocking_removal and isinstance(reasons, list):
            lowered_reasons = " ".join(str(reason).casefold() for reason in reasons)
            blocking_removal = any(marker in lowered_reasons for marker in BLOCKING_REMOVAL_REASON_MARKERS)
        if not blocking_removal:
            continue

        blocked_entry = {
            "id": entry.get("id", ""),
            "title": entry.get("title", ""),
            "url": entry.get("url", ""),
            "removed_on": entry.get("removed_on", ""),
            "reason": reasons[0] if isinstance(reasons, list) and reasons else "Previously removed by resource quality guardrails.",
        }
        entry_id = blocked_entry["id"]
        entry_url = _canonical_url(str(blocked_entry["url"]))
        if entry_id:
            blocked_ids.add(entry_id)
            lookup[entry_id] = blocked_entry
        if entry_url:
            blocked_urls.add(entry_url)
            lookup[entry_url] = blocked_entry

    return blocked_ids, blocked_urls, lookup


def _filter_prior_hard_removals(
    candidates: list[dict[str, Any]],
    blocked_ids: set[str],
    blocked_urls: set[str],
    lookup: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    kept: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for item in candidates:
        rid = str(item.get("id", ""))
        url = _canonical_url(str(item.get("url", "")))
        if rid in blocked_ids or url in blocked_urls:
            previous = lookup.get(url) or lookup.get(rid) or {}
            skipped.append(
                {
                    "id": rid,
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "reason": previous.get("reason", "Matched a prior blocking removal log entry."),
                    "previous_removed_on": previous.get("removed_on", ""),
                }
            )
            continue
        kept.append(item)
    return kept, skipped


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", default="resources/catalog/resources.json")
    parser.add_argument("--output", default="resources/catalog/pending_candidates.json")
    parser.add_argument("--removal-log", default="resources/catalog/removal_log.json")
    parser.add_argument("--limit", type=int, default=15)
    args = parser.parse_args()

    catalog_path = Path(args.catalog)
    output_path = Path(args.output)
    removal_log_path = Path(args.removal_log)

    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    resources = catalog.get("resources", [])
    existing_ids = {resource.get("id", "") for resource in resources if isinstance(resource, dict)}
    existing_urls = {
        _canonical_url(resource.get("url", ""))
        for resource in resources
        if isinstance(resource, dict) and isinstance(resource.get("url"), str)
    }
    blocked_ids, blocked_urls, blocked_lookup = _load_prior_hard_removals(removal_log_path)

    all_candidates: list[dict[str, Any]] = []
    source_errors: list[str] = []
    sources_used: list[str] = []

    fetch_steps = [
        ("kaggle-datasets", lambda: fetch_kaggle_datasets(args.limit)),
        ("huggingface-datasets", lambda: fetch_huggingface("datasets", args.limit)),
        ("huggingface-models", lambda: fetch_huggingface("models", args.limit)),
        ("huggingface-spaces", lambda: fetch_huggingface_spaces(args.limit)),
        ("github-repositories", lambda: fetch_github_pashto_repos(args.limit)),
        ("gitlab-projects", lambda: fetch_gitlab_pashto_projects(args.limit)),
        ("openalex", lambda: fetch_openalex_papers(args.limit)),
        ("crossref", lambda: fetch_crossref_papers(args.limit)),
        ("zenodo", lambda: fetch_zenodo_records(args.limit)),
        ("dataverse", lambda: fetch_dataverse_datasets(args.limit)),
        ("datacite", lambda: fetch_datacite_records(args.limit)),
        ("arxiv", lambda: fetch_arxiv(args.limit)),
        ("semantic-scholar", lambda: fetch_semantic_scholar(args.limit)),
    ]

    for source_name, step in fetch_steps:
        try:
            results = step()
            all_candidates.extend(results)
            sources_used.append(source_name)
        except Exception as exc:  # noqa: BLE001
            source_errors.append(f"{source_name}: {exc}")

    unique_candidates = _dedupe_candidates(all_candidates, existing_ids, existing_urls)
    unique_candidates, skipped_prior_removals = _filter_prior_hard_removals(
        unique_candidates,
        blocked_ids,
        blocked_urls,
        blocked_lookup,
    )
    unique_candidates = sorted(unique_candidates, key=lambda item: item["title"].lower())

    payload: dict[str, Any] = {
        "generated_on": datetime.now(timezone.utc).isoformat(),
        "sources": sources_used,
        "candidate_count": len(unique_candidates),
        "candidates": unique_candidates,
    }
    if source_errors:
        payload["errors"] = source_errors
    if skipped_prior_removals:
        payload["skipped_prior_removals"] = skipped_prior_removals
        payload["warnings"] = [
            f"Skipped {len(skipped_prior_removals)} candidate(s) that matched prior blocking removal log entries."
        ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        try:
            old_payload = json.loads(output_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            old_payload = None
        if isinstance(old_payload, dict):
            old_compare = {key: value for key, value in old_payload.items() if key != "generated_on"}
            new_compare = {key: value for key, value in payload.items() if key != "generated_on"}
            if old_compare == new_compare:
                print(
                    f"Candidate sync complete: {len(unique_candidates)} new candidates, "
                    f"{len(source_errors)} source errors, "
                    f"{len(skipped_prior_removals)} skipped from prior blocking removals, no file changes"
                )
                return 0

    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(
        f"Candidate sync complete: {len(unique_candidates)} new candidates, "
        f"{len(source_errors)} source errors, "
        f"{len(skipped_prior_removals)} skipped from prior blocking removals"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
