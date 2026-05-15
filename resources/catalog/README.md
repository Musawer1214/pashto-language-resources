# 🧾 Resource Catalog

This folder contains machine-readable resource data used by docs and GitHub Pages search.

## 📁 Files

- `resources.json`: canonical verified Pashto resource catalog (source of truth).
- `pending_candidates.json`: automation output for newly discovered candidates.
- `resource.template.json`: starter template for adding a new entry manually.

## 👶 Beginner Workflow (Safe)

1. Discover candidates:
   - `python scripts/sync_resources.py --limit 20`
2. Review candidates in:
   - `resources/catalog/pending_candidates.json`
3. Promote valid entries:
   - `python scripts/promote_candidates.py`
4. Validate + regenerate:
   - `python scripts/validate_resource_catalog.py`
   - `python scripts/generate_resource_views.py`
5. Commit catalog and generated outputs.

## ✅ Promotion Guardrails

- Auto-promotion accepts only valid, non-duplicate entries.
- Auto-promotion rejects candidates whose live pages are hard-missing, deleted, unavailable, empty, or contentless, regardless of source.
- Resources removed for blocking quality reasons are recorded in `removal_log.json` so future syncs do not re-add the same bad ID or URL.
- Keep only Pashto-centric resources.
- Reject entries where Pashto appears only as a side reference.
- Accepted Pashto variants include:
  - `pashto`
  - `pukhto`
  - `pushto`
  - `pakhto`
  - `pashto-script`
