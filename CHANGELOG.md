# Changelog

All notable changes to stapel-taskspecs are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project uses pre-1.0 semver: **minor = breaking**, patch = compatible.

## [0.1.0] - 2026-07-05

Initial release. Schema library for Stapel Studio pipeline artifacts.

### Added
- **JSON Schema v1** (`schemas/`, Draft 2020-12) for the six pipeline
  artifacts — `task_spec`, `task_report`, `spec_patch`, `qa_report`,
  `escalation_question`, `review_finding` — plus the shared `usage_split`.
  Every artifact carries `schema_version: 1` and is forward-compatible
  (unknown top-level fields are accepted, not rejected).
- **Strict five-component usage split** (`usage_split.v1.json`): a closed
  object of exactly `cache_read` / `cache_write` / `fresh_input` / `output` /
  `thinking` (non-negative integers). Referenced by `task_report` and required
  on every report — the split is a protocol condition, not a convenience.
- **Dataclass models** (`models.py`): `TaskSpec`, `TaskReport`, `SpecPatch`,
  `QAReport`, `EscalationQuestion`, `ReviewFinding`, `UsageSplit`. Tolerant
  `from_dict` (unknown fields preserved in `extra` for round-trip fidelity),
  `to_dict`, `validate()` and `parse()`.
- **Validation** (`validation.py`): `validate` / `is_valid` / `iter_errors`
  over a `referencing` registry that resolves the cross-file `usage_split`
  `$ref`. `jsonschema` is imported only here.
- **Markdown + YAML front matter <-> JSON** (`frontmatter.py`):
  `split_front_matter` / `join_front_matter` and TaskSpec-specific
  `taskspec_from_markdown` / `taskspec_to_markdown`.
- Django-free, lazy (PEP 562) package import; `py.typed`.

### Notes
- Risk classes, model names, statuses, severities and failure taxonomies are
  **open** strings/enums with examples — never hardcoded closed sets. Gate
  rules, prompts, anti-cheat detectors and routing thresholds live in the
  private orchestrator, not in these schemas (OSS/moat boundary, studio-design
  §6: "boundaries = schemas").
