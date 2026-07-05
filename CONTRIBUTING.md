# Contributing to stapel-taskspecs

Thanks for helping. This is a schema library: it defines the wire shape of the
Stapel Studio pipeline artifacts. Changes here ripple to every consumer, so the
bar is "would every producer and reader of this artifact agree?"

## Scope

In scope: the JSON Schemas, the dataclass models, validation, and the
markdown/front-matter bridge. **Out of scope** (this is the OSS/moat boundary):
prompts, anti-cheat detectors, routing/escalation policy, gate logic, and any
closed enum of policy values (risk classes, model names, FSM states). Keep
those value sets open — see `MODULE.md`.

## Development

```sh
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
ruff check .
python -m pytest tests/
```

Gates (must be green before merge): `ruff check` (E, F, W; E501 ignored),
`pytest` with the packaged suite, and coverage per `codecov.yml` (patch floor
80%, project ratchet).

## Schema changes

Follow the evolution policy in `MODULE.md`:

- Additive, optional field → patch release, same `schema_version`, add a
  CHANGELOG entry and a test.
- Breaking change (new required field, removal/rename, tightened constraint) →
  a new schema major (`*.v2.json`, `schema_version: 2`), keep the v1 file for a
  deprecation window.

Every behavioural change needs a CHANGELOG entry and a test in the same PR.

## Conduct

By participating you agree to the [Code of Conduct](CODE_OF_CONDUCT.md).
