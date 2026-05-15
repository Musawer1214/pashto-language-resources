# 🔁 Resource Cycle Runbook

Use this runbook when you want a repeatable, safe update process for Pashto resources.

## 🤖 Daily Automation (Already Enabled)

- Workflow: [../.github/workflows/resource_sync.yml](../.github/workflows/resource_sync.yml)
- Schedule: every day at 04:00 UTC
- Automation output:
  - reviews existing resources for stale or low-signal entries
  - updates [../resources/catalog/pending_candidates.json](../resources/catalog/pending_candidates.json)
  - auto-promotes valid non-duplicate entries into [../resources/catalog/resources.json](../resources/catalog/resources.json)
  - regenerates views and search payloads
  - opens a review PR

## 🧭 Manual Run (One Command)

Run from repository root:

```bash
python scripts/run_resource_cycle.py --limit 25
```

This executes:

1. `python scripts/review_existing_resources.py`
2. `python scripts/sync_resources.py --limit 25`
3. `python scripts/promote_candidates.py`
4. `python scripts/validate_resource_catalog.py`
5. `python scripts/generate_resource_views.py`
6. `python scripts/check_links.py`
7. `python -m pytest -q`

## 🔎 Discovery-Only Mode

Use this when you want candidates without immediate promotion:

1. `python scripts/run_resource_cycle.py --discover-only --limit 25`
2. Review [../resources/catalog/pending_candidates.json](../resources/catalog/pending_candidates.json)
3. Promote selected entries with:
   - `python scripts/promote_candidates.py --max-promotions <N>`
4. Regenerate and validate:
   - `python scripts/run_resource_cycle.py --skip-pytest`
5. Commit and push.

## ✅ Guardrails

- Auto-promotion requires dedupe + URL availability + catalog validation.
- Existing entries are removed only for strong reasons, logged in `resources/catalog/removal_log.json`.
- URL availability checks cover every source type. Hard 404/410/451 responses, deleted/unavailable page text, and empty/contentless automated entries block promotion and future re-adds.
- Keep only Pashto-centric resources.
- Generated files must always be committed after catalog changes.

## 🧾 Versioning Reminder

- Version format: `vMAJOR.CODE.RESOURCE`
- Daily bot sync updates are **resource updates**.
- Code or implementation changes increment the **middle figure**.
- Example: `v1.1.1` (code release) -> `v1.1.2` (resource release)
