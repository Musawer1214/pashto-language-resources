from scripts.review_existing_resources import UrlProbe, review_resources


def _resource(*, rid: str, title: str, url: str) -> dict:
    return {
        "id": rid,
        "title": title,
        "url": url,
        "category": "dataset",
        "source": "other",
        "status": "verified",
        "summary": "Resource summary used for catalog review tests.",
        "primary_use": "Testing",
        "tasks": ["nlp"],
        "pashto_evidence": {
            "evidence_text": "Contains Pashto signal in metadata.",
            "evidence_url": url,
            "markers": ["Pashto"],
        },
        "tags": ["pashto", "dataset"],
    }


def test_review_resources_removes_hard_missing_urls() -> None:
    catalog = {
        "version": "1.0.0",
        "updated_on": "2026-02-20",
        "resources": [_resource(rid="dataset-a", title="Pashto A", url="https://example.org/a")],
    }

    def probe(_: str, __: float) -> UrlProbe:
        return UrlProbe(status_code=404, hard_missing=True)

    updated, report = review_resources(catalog, probe_fn=probe)

    assert report["removed"] == 1
    assert updated["resources"] == []
    assert any("hard-missing HTTP status 404" in reason for reason in report["removals"][0]["reasons"])
    assert report["removals"][0]["evidence"]["signal_origin"] == "direct"


def test_review_resources_removes_deleted_non_github_resource() -> None:
    resource = _resource(
        rid="candidate-hf-dataset-deleted",
        title="Pashto Deleted Dataset",
        url="https://huggingface.co/datasets/example/pashto-deleted",
    )
    resource["source"] = "huggingface"
    resource["primary_use"] = "Automated discovery entry for Pashto resource tracking."
    catalog = {"version": "1.0.0", "updated_on": "2026-02-20", "resources": [resource]}

    def probe(_: str, __: float) -> UrlProbe:
        return UrlProbe(status_code=200, content_sample="This dataset has been deleted. Pashto")

    updated, report = review_resources(catalog, probe_fn=probe)

    assert report["removed"] == 1
    assert updated["resources"] == []
    assert any("resource is unavailable" in reason for reason in report["removals"][0]["reasons"])


def test_review_resources_removes_contentless_non_github_candidate() -> None:
    resource = _resource(
        rid="candidate-kaggle-dataset-empty",
        title="Pashto Empty Dataset",
        url="https://www.kaggle.com/datasets/example/pashto-empty",
    )
    resource["source"] = "kaggle"
    resource["primary_use"] = "Automated discovery entry for Pashto resource tracking."
    catalog = {"version": "1.0.0", "updated_on": "2026-02-20", "resources": [resource]}

    def probe(_: str, __: float) -> UrlProbe:
        return UrlProbe(status_code=200, content_sample="No files have been uploaded. Pashto")

    updated, report = review_resources(catalog, probe_fn=probe)

    assert report["removed"] == 1
    assert updated["resources"] == []
    assert any("empty or contentless" in reason for reason in report["removals"][0]["reasons"])


def test_review_resources_keeps_resource_when_probe_is_inconclusive() -> None:
    catalog = {
        "version": "1.0.0",
        "updated_on": "2026-02-20",
        "resources": [_resource(rid="dataset-a", title="Pashto A", url="https://example.org/a")],
    }

    def probe(_: str, __: float) -> UrlProbe:
        return UrlProbe(uncertain_error="timed out")

    updated, report = review_resources(catalog, probe_fn=probe)

    assert report["removed"] == 0
    assert len(updated["resources"]) == 1
    assert len(report["warnings"]) == 1


def test_review_resources_removes_duplicate_urls() -> None:
    catalog = {
        "version": "1.0.0",
        "updated_on": "2026-02-20",
        "resources": [
            _resource(rid="dataset-a", title="Pashto A", url="https://example.org/shared"),
            _resource(rid="dataset-b", title="Pashto B", url="https://example.org/shared"),
        ],
    }

    def probe(_: str, __: float) -> UrlProbe:
        return UrlProbe(status_code=200, content_sample="Pashto")

    updated, report = review_resources(catalog, probe_fn=probe)

    assert report["removed"] == 1
    assert len(updated["resources"]) == 1
    assert any("Duplicate canonical URL" in reason for reason in report["removals"][0]["reasons"])


def test_review_resources_allows_same_url_across_different_categories() -> None:
    dataset = _resource(rid="dataset-a", title="Pashto A", url="https://example.org/shared")
    benchmark = _resource(rid="benchmark-a", title="Pashto A Benchmark", url="https://example.org/shared")
    benchmark["category"] = "benchmark"
    benchmark["tags"] = ["pashto", "benchmark"]
    catalog = {
        "version": "1.0.0",
        "updated_on": "2026-02-20",
        "resources": [dataset, benchmark],
    }

    def probe(_: str, __: float) -> UrlProbe:
        return UrlProbe(status_code=200, content_sample="Pashto")

    updated, report = review_resources(catalog, probe_fn=probe)

    assert report["removed"] == 0
    assert len(updated["resources"]) == 2


def test_review_resources_enforces_pashto_relevance_only_when_enabled() -> None:
    non_pashto = _resource(rid="dataset-x", title="General Dataset", url="https://example.org/general")
    non_pashto["pashto_evidence"]["evidence_text"] = "Generic metadata note."
    non_pashto["pashto_evidence"]["markers"] = ["generic"]
    non_pashto["tags"] = ["dataset", "general"]
    catalog = {"version": "1.0.0", "updated_on": "2026-02-20", "resources": [non_pashto]}

    def probe(_: str, __: float) -> UrlProbe:
        return UrlProbe(status_code=200, content_sample="General language resource")

    updated_relaxed, report_relaxed = review_resources(catalog, probe_fn=probe, enforce_pashto_relevance=False)
    updated_strict, report_strict = review_resources(catalog, probe_fn=probe, enforce_pashto_relevance=True)

    assert report_relaxed["removed"] == 0
    assert len(updated_relaxed["resources"]) == 1
    assert report_strict["removed"] == 1
    assert updated_strict["resources"] == []


def test_review_resources_removes_empty_github_candidate() -> None:
    github_resource = _resource(
        rid="candidate-gh-project-empty",
        title="Example/empty-pashto",
        url="https://github.com/example/empty-pashto",
    )
    github_resource["source"] = "github"
    github_resource["category"] = "project"
    github_resource["tasks"] = []
    github_resource["primary_use"] = "Automated discovery entry for Pashto resource tracking."
    catalog = {"version": "1.0.0", "updated_on": "2026-02-20", "resources": [github_resource]}

    def probe(_: str, __: float) -> UrlProbe:
        return UrlProbe(status_code=200, content_sample="This repository is empty. Pashto")

    updated, report = review_resources(catalog, probe_fn=probe)

    assert report["removed"] == 1
    assert updated["resources"] == []
    assert any("GitHub repository is empty" in reason for reason in report["removals"][0]["reasons"])


def test_review_resources_removes_github_profile_candidate() -> None:
    github_resource = _resource(
        rid="candidate-gh-project-profile",
        title="ExamplePashto/ExamplePashto",
        url="https://github.com/ExamplePashto/ExamplePashto",
    )
    github_resource["source"] = "github"
    github_resource["category"] = "project"
    github_resource["tasks"] = []
    github_resource["summary"] = "Config files for my GitHub profile."
    github_resource["primary_use"] = "Automated discovery entry for Pashto resource tracking."
    catalog = {"version": "1.0.0", "updated_on": "2026-02-20", "resources": [github_resource]}

    def probe(_: str, __: float) -> UrlProbe:
        return UrlProbe(status_code=200, content_sample="Pashto appears on your GitHub profile.")

    updated, report = review_resources(catalog, probe_fn=probe)

    assert report["removed"] == 1
    assert updated["resources"] == []
    assert any("profile/config repository" in reason for reason in report["removals"][0]["reasons"])
