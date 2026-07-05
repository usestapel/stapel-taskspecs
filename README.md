# stapel-taskspecs

Versioned schemas and models for the artifacts that flow through the Stapel
Studio pipeline: a **TaskSpec** goes to an architect, a **TaskReport** comes
back from a runner, a **SpecPatch** amends the project spec, a **QAReport**
records per-criterion acceptance, an **EscalationQuestion** asks a human, and a
**ReviewFinding** captures a falsifiable review claim.

This is a small, **Django-free, pure-Python** library. It carries the *shape*
of the artifacts — fields, types, states — and nothing of the pipeline's
brains. It sits on the OSS side of the OSS/moat boundary: **boundaries are
schemas** (studio-design §6). Prompts, anti-cheat detectors, routing config and
escalation thresholds are not here and never will be.

## Install

```sh
pip install stapel-taskspecs
```

Runtime dependencies are just two: **jsonschema** (validation) and **PyYAML**
(the YAML front-matter header). See "Why these dependencies" below.

## What's in the box

| Artifact | Schema | Model | Purpose |
|---|---|---|---|
| TaskSpec | `schemas/task_spec.v1.json` | `TaskSpec` | unit of work: id, type, goal, criteria, budget, risk, deps |
| TaskReport | `schemas/task_report.v1.json` | `TaskReport` | attempt outcome: status, controls, files, commits, **usage** |
| SpecPatch | `schemas/spec_patch.v1.json` | `SpecPatch` | operations over the project spec + confirmation text |
| QAReport | `schemas/qa_report.v1.json` | `QAReport` | per-criterion pass/fail with screenshot/repro refs |
| EscalationQuestion | `schemas/escalation_question.v1.json` | `EscalationQuestion` | business-language question + options |
| ReviewFinding | `schemas/review_finding.v1.json` | `ReviewFinding` | fingerprint + falsifiable claim + severity |
| UsageSplit | `schemas/usage_split.v1.json` | `UsageSplit` | the strict five-component token split |

Every artifact carries `schema_version: 1`.

## Quickstart

```python
from stapel_taskspecs import TaskSpec, TaskReport, validate, taskspec_from_markdown

# Parse + validate a JSON payload into a typed model
spec = TaskSpec.parse({
    "schema_version": 1,
    "id": "T-001",
    "type": "feature",
    "goal": "CRUD entity: list, create, view and edit",
    "risk": ["validation"],
    "criteria": [{"id": "C1", "text": "Given: empty db; When: POST; Then: 201"}],
    "budget": {"iterations": 3, "wall_min": 20},
})

# Validate a raw dict without building a model
validate(spec.to_dict(), "task_spec")

# Read the repository projection (markdown + YAML front matter)
spec = taskspec_from_markdown(open("TASKS/T-001.md").read())
print(spec.id, spec.criteria)
```

### The five-component usage split is mandatory and closed

`TaskReport.usage` is a `UsageSplit` of **exactly** five non-negative integers —
`cache_read`, `cache_write`, `fresh_input`, `output`, `thinking` — and nothing
else. Every report carries it (report zeros, never omit it). This is a protocol
condition, not a convenience: without a dedicated `thinking` column the
economics of reasoning-class models (thinking tokens billed as output) are
understated.

```python
report = TaskReport.parse({
    "schema_version": 1,
    "task_id": "T-001",
    "status": "done",
    "usage": {"cache_read": 18000, "cache_write": 0,
              "fresh_input": 320, "output": 640, "thinking": 0},
})
report.usage.prompt_tokens  # cache_read + cache_write + fresh_input
```

A missing, extra, negative or non-integer component fails validation.

### Markdown <-> JSON

Tasks live in a project repo as human-readable markdown with a YAML
front-matter header (machine fields up top, prose below); inside the pipeline
everything is JSON validated by schema (system-design §7.17). This library is
the bridge:

```python
from stapel_taskspecs import taskspec_from_markdown, taskspec_to_markdown

spec = taskspec_from_markdown(md_text)   # -> TaskSpec (body kept in .body)
md_text = taskspec_to_markdown(spec)     # -> markdown projection
```

## Forward compatibility

The artifact envelopes are **forward-compatible**: a v1 reader accepts (and
preserves, in `model.extra`) unknown top-level fields a newer producer added,
rather than rejecting the document. The one deliberate exception is
`UsageSplit`, which is closed by design.

## Open by design (OSS/moat boundary)

Risk classes, model names, FSM statuses, severities and failure taxonomies are
**open** strings/enums with documented examples — not hardcoded closed sets. A
consuming host owns those value sets. Gate semantics (red-before-coder,
path-ownership, finding falsifiability) are documented methodology; their
*implementations and detectors* are private. This library is only the wire
shape.

## Why these dependencies

- **jsonschema** — the schemas are the product; a spec-compliant validator is
  the honest way to enforce them, and it resolves the cross-file `usage_split`
  `$ref`.
- **PyYAML** — the front-matter header is YAML, so a YAML parser is
  unavoidable. We parse the header with PyYAML and split the `---` fence with
  the stdlib; we deliberately **do not** add `python-frontmatter` (a whole
  dependency for a ten-line split, with its own metadata conventions we don't
  want).

Import is lazy (PEP 562): `import stapel_taskspecs` pulls in neither jsonschema
nor PyYAML until you touch a validation or front-matter symbol.

## License

MIT.
