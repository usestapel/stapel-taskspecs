"""JSON Schema loading and validation for the taskspecs artifacts.

The schemas ship as package data under ``schemas/``. This module loads them
once, wires cross-file ``$ref`` resolution through a ``referencing`` registry
(so ``task_report`` can reference ``usage_split`` by its ``$id``), and exposes
a single :func:`validate` entry point plus the artifact-name registry.

``jsonschema`` is imported here and only here, so ``import stapel_taskspecs``
and the dataclass/front-matter paths stay dependency-light.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from .errors import SchemaValidationError, UnknownArtifactError

_SCHEMA_DIR = Path(__file__).resolve().parent / "schemas"

#: artifact name -> schema filename. The canonical list of v1 artifacts.
SCHEMA_FILES: dict[str, str] = {
    "task_spec": "task_spec.v1.json",
    "task_report": "task_report.v1.json",
    "spec_patch": "spec_patch.v1.json",
    "qa_report": "qa_report.v1.json",
    "escalation_question": "escalation_question.v1.json",
    "review_finding": "review_finding.v1.json",
    "usage_split": "usage_split.v1.json",
}

#: current schema major version stamped into every artifact.
SCHEMA_VERSION = 1


def artifact_names() -> list[str]:
    """Names of every artifact that has a registered schema."""
    return list(SCHEMA_FILES)


@lru_cache(maxsize=None)
def load_schema(name: str) -> dict[str, Any]:
    """Return the parsed JSON Schema for ``name`` (cached)."""
    try:
        filename = SCHEMA_FILES[name]
    except KeyError:
        raise UnknownArtifactError(
            f"unknown artifact {name!r}; known: {sorted(SCHEMA_FILES)}"
        ) from None
    return json.loads((_SCHEMA_DIR / filename).read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def _registry():
    """A ``referencing`` registry holding every schema keyed by its ``$id``.

    Built once; lets relative ``$ref``s (e.g. ``usage_split.v1.json`` inside
    ``task_report``) resolve against the sibling schema's ``$id``.
    """
    from referencing import Registry, Resource

    resources = []
    for name in SCHEMA_FILES:
        schema = load_schema(name)
        resources.append((schema["$id"], Resource.from_contents(schema)))
    return Registry().with_resources(resources)


@lru_cache(maxsize=None)
def _validator(name: str):
    from jsonschema import Draft202012Validator

    schema = load_schema(name)
    return Draft202012Validator(schema, registry=_registry())


def iter_errors(instance: Any, name: str) -> list[str]:
    """Return a sorted list of human-readable validation error lines.

    Empty list means the instance is valid. Does not raise on invalidity —
    use :func:`validate` for the raising variant.
    """
    validator = _validator(name)
    lines = []
    for err in sorted(validator.iter_errors(instance), key=lambda e: list(e.path)):
        loc = "/".join(str(p) for p in err.path) or "<root>"
        lines.append(f"{loc}: {err.message}")
    return lines


def is_valid(instance: Any, name: str) -> bool:
    """True if ``instance`` validates against the ``name`` schema."""
    return not iter_errors(instance, name)


def validate(instance: Any, name: str) -> None:
    """Validate ``instance`` against the ``name`` schema.

    Raises :class:`~stapel_taskspecs.errors.SchemaValidationError` with the
    collected error lines on any failure; returns ``None`` on success.
    """
    errors = iter_errors(instance, name)
    if errors:
        raise SchemaValidationError(
            f"{name} failed schema validation ({len(errors)} error(s))",
            errors=errors,
        )
