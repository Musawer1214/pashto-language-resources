# 🤖 Resource Automation

This project uses automation to keep Pashto, Pukhto, and Pushto AI resources current without lowering quality.

## 🎯 What This Automation Does

- Finds new Pashto-relevant resources from trusted public endpoints.
- Keeps one canonical machine-readable catalog.
- Promotes only candidates that pass validation + deduplication.
- Generates two search payloads:
  - technical resources (non-paper)
  - papers/documentation resources

## 📁 Core Files

- Canonical verified catalog: [resources/catalog/resources.json on GitHub](https://github.com/Musawer1214/pashto-language-resources/blob/main/resources/catalog/resources.json)
- Candidate feed: [resources/catalog/pending_candidates.json on GitHub](https://github.com/Musawer1214/pashto-language-resources/blob/main/resources/catalog/pending_candidates.json)
- Catalog schema: [resources/schema/resource.schema.json on GitHub](https://github.com/Musawer1214/pashto-language-resources/blob/main/resources/schema/resource.schema.json)
- Contract schemas: [resources/schema/ on GitHub](https://github.com/Musawer1214/pashto-language-resources/tree/main/resources/schema)
- Technical search export: [search/resources.json](search/resources.json)
- Papers search export: [papers/resources.json](papers/resources.json)

## 🧰 Scripts (Manual Use)

- Validate catalog: `python scripts/validate_resource_catalog.py`
- Validate catalog-adjacent contracts: `python scripts/validate_repo_contracts.py --require-jsonschema`
- Generate README + search outputs: `python scripts/generate_resource_views.py`
- Review existing resources: `python scripts/review_existing_resources.py`
- Discover new candidates: `python scripts/sync_resources.py --limit 20`
- Promote valid candidates: `python scripts/promote_candidates.py`
- Audit non-destructive quality signals: `python scripts/audit_resource_pipeline.py`
- Full cycle wrapper: `python scripts/run_resource_cycle.py --limit 25`

## ⚙️ GitHub Actions (Automatic Use)

- CI workflow: `.github/workflows/ci.yml`
  - validates catalog
  - validates catalog-adjacent contracts
  - checks generated files
  - checks markdown links
  - runs tests
- Daily resource workflow: `.github/workflows/resource_sync.yml`
  - audits existing entries
  - discovers candidates
  - auto-promotes valid entries
  - regenerates views/search payloads
  - opens a PR for review

## 🔄 Promotion Flow (Simple)

1. Review current resources for stale links.
2. Sync candidates into `pending_candidates.json`.
3. Promote only high-confidence, valid, non-duplicate, reachable candidates.
4. Regenerate outputs and validate.
5. Review and merge.

## 📚 Related Guide

- Full runbook: [resource_cycle_runbook.md](resource_cycle_runbook.md)

## Quality Guardrails

- Existing resources are removed only with strong evidence: hard-missing HTTP status, deleted/unavailable page text, duplicate IDs/URLs, empty/contentless automated entries, or missing Pashto relevance when strict review is enabled.
- New candidates are auto-promoted only after the same URL probe rules pass. Empty pages, deleted records, and contentless repositories/datasets are left out for every source, not only GitHub.
- Removed resources are logged in `resources/catalog/removal_log.json`; future syncs skip candidates that match those blocked IDs or URLs so bad entries are not re-added by the daily workflow.
