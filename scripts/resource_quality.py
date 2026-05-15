"""Shared Pashto resource quality and signal helpers."""

from __future__ import annotations

import re
from typing import Any


AUTOMATED_PRIMARY_USE = "Automated discovery entry for Pashto resource tracking."
PLACEHOLDER_PRIMARY_USE = "Needs maintainer review before promotion to verified catalog."
PASHTO_PUSHTO_WORD_RE = re.compile(r"(?<![a-z0-9])pushto(?![a-z0-9])")
PASHTO_CODE_RE = re.compile(r"\b(ps(_af)?|pus|pbt[_-]?arab)\b")
PASHTO_SCRIPT_MARKERS = ("\u067e\u069a\u062a\u0648", "\u067e\u0634\u062a\u0648")
GENERIC_DISCOVERY_SUMMARY_PREFIXES = (
    "candidate dataset returned from",
    "candidate model returned from",
    "candidate paper returned from",
    "candidate benchmark returned from",
    "candidate project returned from",
    "candidate code returned from",
    "candidate tool returned from",
    "pashto language technology paper discovered from",
    "pashto language technology project discovered from",
    "pashto language technology resource discovered from",
)
HIGH_CONFIDENCE_SOURCES = {
    "mozilla",
    "huggingface",
    "github",
    "gitlab",
    "zenodo",
    "dataverse",
    "arxiv",
}
REPOSITORY_SOURCES = {"github", "gitlab"}


def contains_pashto_marker(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    lowered = value.casefold()
    if any(marker in lowered for marker in ("pashto", "pukhto", "pakhto")):
        return True
    if PASHTO_PUSHTO_WORD_RE.search(lowered):
        return True
    if PASHTO_CODE_RE.search(lowered):
        return True
    return any(marker in value for marker in PASHTO_SCRIPT_MARKERS)


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str) and item.strip()]
    return []


def resource_has_metadata_pashto_signal(resource: dict[str, Any]) -> bool:
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
        values.extend(_string_list(evidence.get("markers")))

    return any(contains_pashto_marker(value) for value in values)


def resource_has_direct_pashto_signal(resource: dict[str, Any]) -> bool:
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
        values.extend(_string_list(evidence.get("markers")))

    return any(contains_pashto_marker(value) for value in values)


def resource_has_generic_summary(resource: dict[str, Any]) -> bool:
    summary = str(resource.get("summary", "")).strip().casefold()
    return any(summary.startswith(prefix) for prefix in GENERIC_DISCOVERY_SUMMARY_PREFIXES)


def resource_has_placeholder_primary_use(resource: dict[str, Any]) -> bool:
    primary_use = str(resource.get("primary_use", "")).strip()
    return primary_use in {PLACEHOLDER_PRIMARY_USE, AUTOMATED_PRIMARY_USE}


def resource_is_candidate_like(resource: dict[str, Any]) -> bool:
    rid = resource.get("id")
    if isinstance(rid, str) and rid.startswith("candidate-"):
        return True
    if resource_has_placeholder_primary_use(resource):
        return True
    tags = resource.get("tags")
    return isinstance(tags, list) and "candidate" in tags


def resource_signal_origin(resource: dict[str, Any]) -> str:
    if resource_has_direct_pashto_signal(resource):
        return "direct"
    if resource_has_metadata_pashto_signal(resource):
        return "metadata"
    return "none"


def resource_quality_flags(resource: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    if resource_is_candidate_like(resource):
        flags.append("automated_discovery")
    if resource_has_placeholder_primary_use(resource):
        flags.append("placeholder_primary_use")
    if resource_has_generic_summary(resource):
        flags.append("generic_summary")
    if not _string_list(resource.get("tasks")):
        flags.append("missing_tasks")
    if resource_signal_origin(resource) == "metadata":
        flags.append("metadata_only_pashto_signal")
    return flags


def resource_review_state(resource: dict[str, Any]) -> str:
    status = str(resource.get("status", "")).strip() or "unknown"
    if status == "candidate":
        return "candidate"
    if status == "verified" and resource_is_candidate_like(resource):
        return "automated_verified"
    return status


def normalized_title(value: str) -> str:
    lowered = value.casefold()
    lowered = re.sub(r"[\W_]+", " ", lowered, flags=re.UNICODE)
    return re.sub(r"\s+", " ", lowered).strip()


def assess_candidate_confidence(resource: dict[str, Any]) -> tuple[str, list[str]]:
    signal_origin = resource_signal_origin(resource)
    source = str(resource.get("source", "")).strip().casefold()
    tasks = _string_list(resource.get("tasks"))
    reasons: list[str] = []

    if signal_origin == "none":
        return "low", ["missing_pashto_signal"]

    if signal_origin == "direct":
        reasons.append("direct_pashto_signal")
    else:
        reasons.append("metadata_only_pashto_signal")

    if source in HIGH_CONFIDENCE_SOURCES:
        reasons.append("trusted_source")
    if tasks:
        reasons.append("task_tagged")
    if resource_has_generic_summary(resource):
        reasons.append("generic_discovery_summary")
    if not tasks:
        reasons.append("missing_tasks")

    if source in REPOSITORY_SOURCES and not tasks:
        reasons.append("repository_candidate_missing_tasks")
        return "review", reasons

    if signal_origin == "direct" and (source in HIGH_CONFIDENCE_SOURCES or tasks):
        return "high", reasons
    if signal_origin == "direct":
        return "review", reasons
    return "low", reasons
