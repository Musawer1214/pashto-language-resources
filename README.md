---
license: apache-2.0
language:
- ps
- en
tags:
- pashto
- pukhto
- pushto
- asr
- tts
- nlp
- machine-translation
- language-resources
- low-resource-languages
- speech-recognition
---

# Pashto Language Resources Hub

`pashto-language-resources` is an open catalog for Pashto language technology.
It helps people find and maintain Pashto datasets, models, papers, benchmarks,
code, and tools for ASR, TTS, NLP, and machine translation.

This repository is not a single model or app. It is a verified resource index,
search site, and maintenance workflow for keeping Pashto AI resources easier to
discover and review.

## Start Here

- Search technical resources: [Pashto Resource Search](https://musawer1214.github.io/pashto-language-resources/search/)
- Search papers and documentation: [Pashto Papers Search](https://musawer1214.github.io/pashto-language-resources/papers/)
- Browse the project site: [Pashto Language Resources Hub](https://musawer1214.github.io/pashto-language-resources/)
- Read contributor docs: [docs/README.md](docs/README.md)

## What You Can Find

- Datasets for speech, text, OCR, translation, and NLP work.
- Models and demos hosted on public platforms.
- Benchmarks and evaluation references.
- Papers and documentation related to Pashto language technology.
- Code projects and tools that are relevant to Pashto processing.

For the generated catalog by category, see [resources/README.md](resources/README.md).
For catalog rules and review guidance, see [docs/resource_catalog.md](docs/resource_catalog.md).

## Common Use Cases

Use the search pages if you want to quickly find an existing Pashto resource.
Use the `resources/` catalog if you want machine-readable data or category
README files. Use the scripts only if you are maintaining the catalog or opening
a contribution.

Popular entry points:

- [Pashto datasets](docs/pashto_datasets.md)
- [Pashto ASR resources](docs/pashto_asr.md)
- [Pashto TTS resources](docs/pashto_tts.md)
- [Resource automation guide](docs/resource_automation.md)

## Repository Map

- `resources/`: verified external resources and generated category indexes.
- `docs/`: GitHub Pages content, search pages, and project documentation.
- `data/`: normalization seeds and dataset workflow notes.
- `asr/`: speech recognition notes and future baseline workspace.
- `tts/`: text-to-speech notes and future baseline workspace.
- `benchmarks/`: result schemas and evaluation templates.
- `scripts/`: validation, sync, promotion, and generation tools.

## Local Setup

Install the project from the repository root:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Useful checks:

```bash
python scripts/validate_resource_catalog.py
python scripts/generate_resource_views.py
python scripts/validate_repo_contracts.py --require-jsonschema
python scripts/check_links.py
python -m pytest -q
```

## How Updates Work

The catalog has both manual review and automation:

- Daily GitHub Actions discover new candidates.
- Bad or empty resources are filtered out before promotion.
- Valid, non-duplicate resources can be promoted into `resources/catalog/resources.json`.
- Generated category pages and search payloads are rebuilt from the catalog.

More detail is in [docs/resource_cycle_runbook.md](docs/resource_cycle_runbook.md).

## Contributing

- Contribution guide: [CONTRIBUTING.md](CONTRIBUTING.md)
- Community communication: [community/COMMUNICATION.md](community/COMMUNICATION.md)
- Resource addition guide: [docs/resource_catalog.md](docs/resource_catalog.md)

## Project References

- Purpose: [PROJECT_PURPOSE.md](PROJECT_PURPOSE.md)
- Roadmap: [ROADMAP.md](ROADMAP.md)
- Citation metadata: [CITATION.cff](CITATION.cff)
- Hugging Face mirror: [Musawer14/pashto-language-resources](https://huggingface.co/Musawer14/pashto-language-resources)
- Release notes index: [docs/releases/README.md](docs/releases/README.md)
- Changelog: [CHANGELOG.md](CHANGELOG.md)

## License

This project is released under the Apache 2.0 license. See [LICENSE](LICENSE).
