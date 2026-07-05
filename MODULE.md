# stapel-taskspecs — MODULE.md

Agent-facing map of this library: what it provides, its extension points, and
anti-patterns. Use it to classify a desired change as **app-layer usage** vs
**upstream contribution**. This is an **L1 library** (per
`docs/library-standard.md`): importable by anyone, Django-free, with no comm
surface, no settings namespace, no migrations, no service identity. It is a
schema library — the *structure* half of the OSS/moat boundary (studio-design
§6: "boundaries = schemas").

- Package: `stapel-taskspecs` (PyPI), Python package `stapel_taskspecs`.
- Depends only on `jsonschema` and `PyYAML`. No `stapel-core`, no Django.
- Consumers: the private studio-orchestrator (canonical Task store),
  stapel-runner-protocol (SN-2) messages carry these artifacts, and any OSS
  consumer that speaks the pipeline wire format.

## What this library provides

| Area | Contents |
|---|---|
| Schemas (`schemas/`) | Draft 2020-12 JSON Schema v1 for `task_spec`, `task_report`, `spec_patch`, `qa_report`, `escalation_question`, `review_finding`, and the shared `usage_split`. Each artifact envelope has `schema_version: const 1` and accepts unknown top-level fields (forward-compat). `usage_split` is `additionalProperties: false` — closed by design. |
| Models (`models.py`) | Dataclasses `TaskSpec`, `TaskReport`, `SpecPatch`, `QAReport`, `EscalationQuestion`, `ReviewFinding`, `UsageSplit`. Each has tolerant `from_dict` (unknown keys → `.extra`), `to_dict`, `validate()`, and `parse(data, *, validate=True)`. `MODELS` maps artifact name → class. |
| Validation (`validation.py`) | `validate` / `is_valid` / `iter_errors` (name-addressed), `load_schema`, `artifact_names`, `SCHEMA_FILES`, `SCHEMA_VERSION`. A `referencing` registry resolves the cross-file `usage_split` `$ref` in `task_report`. Only this module imports `jsonschema`. |
| Front matter (`frontmatter.py`) | `split_front_matter` / `join_front_matter` / `has_front_matter` (generic), `taskspec_from_markdown` / `taskspec_to_markdown` (TaskSpec projection). Only this module imports `yaml`. |
| Errors (`errors.py`) | `TaskSpecsError` base; `SchemaValidationError` (with `.errors` lines), `FrontMatterError`, `UnknownArtifactError`. |
| Public API (`__init__.py`, PEP 562 lazy) | The names above, re-exported lazily so `import stapel_taskspecs` stays stdlib-only until a symbol is touched. |

## Extension points

This library has no runtime seams (no settings, no registries) — its extension
model is the **schema shape itself**:

1. **Open value sets.** `type`, `status`, `risk[]`, `failure_type`,
   `severity`, control statuses and `op` are open strings/enums with `examples`,
   not `enum` constraints. A host adds its own risk classes, statuses or
   failure labels **without changing this library** — validation accepts them.
   This is deliberate: closed enums here would encode private routing policy
   into an OSS schema.
2. **Forward compatibility.** Artifact envelopes accept unknown top-level
   fields; models preserve them in `.extra` and re-emit them on `to_dict`. A
   newer producer can add fields a v1 reader will carry through untouched.
3. **Schema evolution policy** (pre-1.0: minor = breaking):
   - Additive, optional fields → patch release, same `schema_version`.
   - A new required field, a removed/renamed field, or a tightened constraint
     → **new schema major** (`task_spec.v2.json`, `schema_version: 2`) with the
     v1 file kept for a deprecation window. Never mutate a shipped v1 schema in
     a breaking way.
   - `usage_split` is intentionally closed; adding a sixth component is a
     breaking (v2) change by construction.

## Anti-patterns

- **Do not encode gate logic in the schema.** "A blocker must have a red repro
  test", "tests must be red before the coder", "two review cycles max" are
  orchestrator gate rules, not schema constraints. `review_finding` therefore
  makes `repro_test_path` optional. Cross-field/stateful gate rules belong in
  the private orchestrator.
- **Do not add closed enums for policy values.** Hardcoding the risk-class or
  model list, or the FSM state set, into an OSS schema leaks moat policy and
  breaks hosts with different value sets. Keep them open with examples.
- **Do not omit the usage split or collapse it.** Report all five components
  (zeros are fine). A partial split silently understates reasoning-class cost.
- **Do not pull in `python-frontmatter`.** The `---` fence split is stdlib +
  PyYAML; a second front-matter dependency is unjustified.

## App-layer usage vs upstream contribution

Litmus: *does the change alter the wire shape of an artifact every consumer
sees?*

- **App-layer (no contribution):** attach host-specific data via unknown
  fields (preserved in `.extra`), use your own `risk`/`status`/`failure_type`
  values, wrap models in your own domain types. None of this touches this
  library.
- **Upstream (contribute here):** a genuinely new shared field on an artifact,
  a new artifact type in the pipeline contract, or a fix to a schema/model bug.
  Additive → patch; breaking → a new schema major per the evolution policy.
