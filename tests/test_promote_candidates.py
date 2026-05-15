from datetime import date

import scripts.promote_candidates as promote_module
from scripts.promote_candidates import PLACEHOLDER_PRIMARY_USE, promote_candidates
from scripts.review_existing_resources import UrlProbe


def _catalog() -> dict:
    return {
        "version": "1.0.1",
        "updated_on": "2026-02-18",
        "resources": [
            {
                "id": "dataset-existing",
                "title": "Pashto Existing Dataset",
                "url": "https://example.org/pashto-existing",
                "category": "dataset",
                "source": "other",
                "status": "verified",
                "summary": "Existing Pashto dataset used as baseline for dedupe checks.",
                "primary_use": "Testing",
                "tasks": ["asr"],
                "pashto_evidence": {
                    "evidence_text": "Includes Pashto split.",
                    "evidence_url": "https://example.org/pashto-existing",
                    "markers": ["pashto"],
                },
                "tags": ["pashto", "dataset"],
            }
        ],
    }


def _candidate(*, rid: str, title: str, url: str, category: str = "dataset") -> dict:
    return {
        "id": rid,
        "title": title,
        "url": url,
        "category": category,
        "source": "huggingface",
        "status": "candidate",
        "summary": "Candidate entry for automated promotion tests.",
        "primary_use": PLACEHOLDER_PRIMARY_USE,
        "tasks": ["asr"],
        "pashto_evidence": {
            "evidence_text": "Contains explicit Pashto marker in evidence text.",
            "evidence_url": url,
            "markers": ["pashto"],
        },
        "tags": ["pashto", "candidate"],
    }


def test_promote_candidates_promotes_valid_non_duplicate_entries() -> None:
    catalog = _catalog()
    pending = {
        "candidate_count": 1,
        "candidates": [
            _candidate(
                rid="dataset-new",
                title="Pashto New Dataset",
                url="https://example.org/pashto-new",
            )
        ],
    }

    promoted, stats = promote_candidates(catalog, pending)

    assert len(promoted) == 1
    assert stats["promoted"] == 1
    assert catalog["updated_on"] == date.today().isoformat()
    assert catalog["resources"][-1]["status"] == "verified"
    assert catalog["resources"][-1]["primary_use"] == "Cataloged Pashto resource discovered through the automated intake pipeline."
    assert "candidate" not in catalog["resources"][-1]["tags"]


def test_promote_candidates_skips_duplicates_and_invalid_entries() -> None:
    catalog = _catalog()
    invalid = _candidate(
        rid="model-invalid",
        title="Pashto Invalid Model",
        url="https://example.org/pashto-model-invalid",
        category="model",
    )
    invalid["pashto_evidence"]["markers"] = []

    pending = {
        "candidate_count": 3,
        "candidates": [
            _candidate(
                rid="dataset-existing",
                title="Pashto Duplicate ID",
                url="https://example.org/new-url",
            ),
            _candidate(
                rid="dataset-url-duplicate",
                title="Pashto Duplicate URL",
                url="https://example.org/pashto-existing",
            ),
            invalid,
        ],
    }

    promoted, stats = promote_candidates(catalog, pending)

    assert promoted == []
    assert stats["promoted"] == 0
    assert stats["duplicate"] == 2
    assert stats["invalid"] == 1
    assert stats["needs_review"] == 0
    assert catalog["updated_on"] == "2026-02-18"
    assert len(catalog["resources"]) == 1


def test_promote_candidates_respects_max_promotions() -> None:
    catalog = _catalog()
    pending = {
        "candidate_count": 2,
        "candidates": [
            _candidate(
                rid="dataset-new-a",
                title="Pashto New Dataset A",
                url="https://example.org/pashto-new-a",
            ),
            _candidate(
                rid="dataset-new-b",
                title="Pashto New Dataset B",
                url="https://example.org/pashto-new-b",
            ),
        ],
    }

    promoted, stats = promote_candidates(catalog, pending, max_promotions=1)

    assert len(promoted) == 1
    assert stats["promoted"] == 1
    assert len(catalog["resources"]) == 2


def test_promote_candidates_skips_unavailable_when_url_check_enabled(monkeypatch) -> None:
    catalog = _catalog()
    pending = {
        "candidate_count": 1,
        "candidates": [
            _candidate(
                rid="dataset-unavailable",
                title="Pashto Unavailable Dataset",
                url="https://example.org/pashto-unavailable",
            )
        ],
    }

    monkeypatch.setattr(
        promote_module,
        "_candidate_url_unavailable",
        lambda *_args, **_kwargs: True,
    )

    promoted, stats = promote_candidates(catalog, pending, verify_urls=True)

    assert promoted == []
    assert stats["promoted"] == 0
    assert stats["unavailable"] == 1


def test_promote_candidates_skips_contentless_non_github_candidate(monkeypatch) -> None:
    catalog = _catalog()
    candidate = _candidate(
        rid="candidate-hf-dataset-empty",
        title="Pashto Empty Dataset",
        url="https://huggingface.co/datasets/example/pashto-empty",
    )
    candidate["source"] = "huggingface"
    pending = {"candidate_count": 1, "candidates": [candidate]}

    monkeypatch.setattr(
        promote_module,
        "probe_resource_url",
        lambda *_args, **_kwargs: UrlProbe(status_code=200, content_sample="No files have been uploaded. Pashto"),
    )

    promoted, stats = promote_candidates(catalog, pending, verify_urls=True)

    assert promoted == []
    assert stats["promoted"] == 0
    assert stats["unavailable"] == 1


def test_promote_candidates_skips_deleted_non_github_candidate(monkeypatch) -> None:
    catalog = _catalog()
    candidate = _candidate(
        rid="candidate-zenodo-dataset-deleted",
        title="Pashto Deleted Dataset",
        url="https://zenodo.org/records/123",
    )
    candidate["source"] = "zenodo"
    pending = {"candidate_count": 1, "candidates": [candidate]}

    monkeypatch.setattr(
        promote_module,
        "probe_resource_url",
        lambda *_args, **_kwargs: UrlProbe(status_code=200, content_sample="This resource has been deleted. Pashto"),
    )

    promoted, stats = promote_candidates(catalog, pending, verify_urls=True)

    assert promoted == []
    assert stats["promoted"] == 0
    assert stats["unavailable"] == 1


def test_promote_candidates_leaves_review_confidence_entries_pending_by_default() -> None:
    catalog = _catalog()
    review_candidate = _candidate(
        rid="paper-review",
        title="Pashto Review Paper",
        url="https://example.org/pashto-review-paper",
        category="paper",
    )
    review_candidate["source"] = "other"
    review_candidate["summary"] = "Candidate paper returned from Semantic Scholar search for Pashto."
    review_candidate["tasks"] = []
    pending = {"candidate_count": 1, "candidates": [review_candidate]}

    promoted, stats = promote_candidates(catalog, pending)

    assert promoted == []
    assert stats["needs_review"] == 1


def test_promote_candidates_leaves_untagged_github_candidates_pending() -> None:
    catalog = _catalog()
    github_candidate = _candidate(
        rid="candidate-gh-project-pashto-example",
        title="Example/pashto-project",
        url="https://github.com/example/pashto-project",
        category="project",
    )
    github_candidate["source"] = "github"
    github_candidate["tasks"] = []
    github_candidate["summary"] = "Pashto project discovered from GitHub metadata."
    pending = {"candidate_count": 1, "candidates": [github_candidate]}

    promoted, stats = promote_candidates(catalog, pending)

    assert promoted == []
    assert stats["needs_review"] == 1


def test_promote_candidates_can_allow_review_confidence_entries() -> None:
    catalog = _catalog()
    review_candidate = _candidate(
        rid="paper-review",
        title="Pashto Review Paper",
        url="https://example.org/pashto-review-paper",
        category="paper",
    )
    review_candidate["source"] = "other"
    review_candidate["summary"] = "Candidate paper returned from Semantic Scholar search for Pashto."
    review_candidate["tasks"] = []
    pending = {"candidate_count": 1, "candidates": [review_candidate]}

    promoted, stats = promote_candidates(catalog, pending, allow_review_confidence=True)

    assert len(promoted) == 1
    assert stats["needs_review"] == 0
