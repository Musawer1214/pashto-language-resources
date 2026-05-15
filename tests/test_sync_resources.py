import json
from pathlib import Path

import scripts.sync_resources as sync_module


FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "sync_resources"


def _fixture(name: str) -> object:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_fetch_huggingface_filters_low_signal_and_non_pashto_results(monkeypatch) -> None:
    payload = _fixture("huggingface_datasets.json")
    calls: list[str] = []

    def fake_fetch_json(url: str, **_kwargs: object) -> object:
        calls.append(url)
        return payload

    monkeypatch.setattr(sync_module, "_fetch_json", fake_fetch_json)

    results = sync_module.fetch_huggingface("datasets", limit=10)

    assert len(calls) == len(sync_module.PASHTO_QUERY_TERMS)
    assert [item["id"] for item in results] == ["candidate-hf-dataset-pashtoorg-pashto-corpus"]
    assert results[0]["url"] == "https://huggingface.co/datasets/PashtoOrg/Pashto-Corpus"
    assert results[0]["category"] == "dataset"


def test_fetch_github_pashto_repos_classifies_code_and_project_from_fixture(monkeypatch) -> None:
    payload = _fixture("github_repositories.json")

    monkeypatch.setattr(sync_module, "_fetch_json", lambda *_args, **_kwargs: payload)

    results = sync_module.fetch_github_pashto_repos(limit=10)

    assert [item["id"] for item in results] == [
        "candidate-gh-code-pashto-org-pashto-asr-toolkit",
        "candidate-gh-project-pashto-org-pashto-education-hub",
    ]
    assert [item["category"] for item in results] == ["code", "project"]
    assert results[0]["tags"][:4] == ["pashto", "candidate", "code", "github"]


def test_fetch_datacite_records_maps_resource_types_and_strips_html(monkeypatch) -> None:
    payload = _fixture("datacite_records.json")

    monkeypatch.setattr(sync_module, "_fetch_json", lambda *_args, **_kwargs: payload)

    results = sync_module.fetch_datacite_records(limit=10)

    assert [item["id"] for item in results] == [
        "candidate-datacite-dataset-pashto-speech-dataset",
        "candidate-datacite-code-pashto-ocr-toolkit",
        "candidate-datacite-paper-pashto-acoustic-modeling",
    ]
    assert [item["category"] for item in results] == ["dataset", "code", "paper"]
    assert results[0]["url"] == "https://doi.org/10.1234/pashto-dataset"
    assert results[0]["summary"] == "Curated Pashto speech corpus."


def test_sync_skips_candidates_that_match_prior_hard_removals(tmp_path) -> None:
    removal_log = {
        "updated_on": "2026-03-20",
        "entries": [
            {
                "removed_on": "2026-03-19T00:00:00Z",
                "id": "candidate-kaggle-pashto-dead",
                "title": "Dead candidate",
                "url": "https://example.org/dead",
                "reasons": ["URL returned hard-missing HTTP status 404."],
                "evidence": {"status_code": 404},
            }
        ],
    }
    path = tmp_path / "removal_log.json"
    path.write_text(json.dumps(removal_log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    blocked_ids, blocked_urls, lookup = sync_module._load_prior_hard_removals(path)
    kept, skipped = sync_module._filter_prior_hard_removals(
        [
            {
                "id": "candidate-kaggle-pashto-dead",
                "title": "Dead candidate",
                "url": "https://example.org/dead",
            },
            {
                "id": "candidate-hf-dataset-live",
                "title": "Pashto Live Dataset",
                "url": "https://example.org/live",
            },
        ],
        blocked_ids,
        blocked_urls,
        lookup,
    )

    assert [item["id"] for item in kept] == ["candidate-hf-dataset-live"]
    assert skipped[0]["id"] == "candidate-kaggle-pashto-dead"


def test_sync_skips_candidates_that_match_prior_contentless_removals(tmp_path) -> None:
    removal_log = {
        "updated_on": "2026-05-15",
        "entries": [
            {
                "removed_on": "2026-05-15T00:00:00Z",
                "id": "candidate-hf-dataset-empty",
                "title": "Pashto Empty Dataset",
                "url": "https://huggingface.co/datasets/example/pashto-empty",
                "reasons": ["Automated candidate live page appears empty or contentless."],
                "evidence": {"status_code": 200},
            }
        ],
    }
    path = tmp_path / "removal_log.json"
    path.write_text(json.dumps(removal_log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    blocked_ids, blocked_urls, lookup = sync_module._load_prior_hard_removals(path)
    kept, skipped = sync_module._filter_prior_hard_removals(
        [
            {
                "id": "candidate-hf-dataset-empty",
                "title": "Pashto Empty Dataset",
                "url": "https://huggingface.co/datasets/example/pashto-empty",
            },
            {
                "id": "candidate-hf-dataset-live",
                "title": "Pashto Live Dataset",
                "url": "https://huggingface.co/datasets/example/pashto-live",
            },
        ],
        blocked_ids,
        blocked_urls,
        lookup,
    )

    assert [item["id"] for item in kept] == ["candidate-hf-dataset-live"]
    assert skipped[0]["id"] == "candidate-hf-dataset-empty"
