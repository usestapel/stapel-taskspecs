"""stapel-taskspecs — versioned schemas + models for Stapel Studio pipeline artifacts.

A pure-Python, Django-free schema library: JSON Schema (``schemas/``) and
dataclass models with schema validation for the v1 pipeline artifacts
(TaskSpec, TaskReport, SpecPatch, QAReport, EscalationQuestion, ReviewFinding),
a strict five-component usage split, and markdown+front-matter <-> JSON
conversion.

This is a schema library on the OSS/moat boundary: it carries the *structure*
of the artifacts (fields, types, states) and nothing of the pipeline's brains
(no prompts, no anti-cheat rules, no routing config, no thresholds). Risk
classes, model names, statuses and failure taxonomies are open strings/enums
with examples, never hardcoded closed sets.

Imports are lazy (PEP 562): ``import stapel_taskspecs`` pulls in nothing but
the stdlib until you touch a name, so validation (``jsonschema``) and
front-matter parsing (``PyYAML``) load only when used.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

__version__ = "0.1.0"

__all__ = [
    "__version__",
    # models
    "TaskSpec",
    "TaskReport",
    "SpecPatch",
    "QAReport",
    "EscalationQuestion",
    "ReviewFinding",
    "UsageSplit",
    "MODELS",
    # validation
    "validate",
    "is_valid",
    "iter_errors",
    "load_schema",
    "artifact_names",
    "SCHEMA_FILES",
    "SCHEMA_VERSION",
    # front matter
    "split_front_matter",
    "join_front_matter",
    "has_front_matter",
    "taskspec_from_markdown",
    "taskspec_to_markdown",
    # errors
    "TaskSpecsError",
    "SchemaValidationError",
    "FrontMatterError",
    "UnknownArtifactError",
]

_LAZY = {
    "TaskSpec": "models",
    "TaskReport": "models",
    "SpecPatch": "models",
    "QAReport": "models",
    "EscalationQuestion": "models",
    "ReviewFinding": "models",
    "UsageSplit": "models",
    "MODELS": "models",
    "validate": "validation",
    "is_valid": "validation",
    "iter_errors": "validation",
    "load_schema": "validation",
    "artifact_names": "validation",
    "SCHEMA_FILES": "validation",
    "SCHEMA_VERSION": "validation",
    "split_front_matter": "frontmatter",
    "join_front_matter": "frontmatter",
    "has_front_matter": "frontmatter",
    "taskspec_from_markdown": "frontmatter",
    "taskspec_to_markdown": "frontmatter",
    "TaskSpecsError": "errors",
    "SchemaValidationError": "errors",
    "FrontMatterError": "errors",
    "UnknownArtifactError": "errors",
}


def __getattr__(name: str):
    module = _LAZY.get(name)
    if module is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    import importlib

    mod = importlib.import_module(f".{module}", __name__)
    return getattr(mod, name)


def __dir__() -> list[str]:
    return sorted(__all__)


if TYPE_CHECKING:  # give type checkers/IDEs the real symbols
    from .errors import (
        FrontMatterError,
        SchemaValidationError,
        TaskSpecsError,
        UnknownArtifactError,
    )
    from .frontmatter import (
        has_front_matter,
        join_front_matter,
        split_front_matter,
        taskspec_from_markdown,
        taskspec_to_markdown,
    )
    from .models import (
        MODELS,
        EscalationQuestion,
        QAReport,
        ReviewFinding,
        SpecPatch,
        TaskReport,
        TaskSpec,
        UsageSplit,
    )
    from .validation import (
        SCHEMA_FILES,
        SCHEMA_VERSION,
        artifact_names,
        is_valid,
        iter_errors,
        load_schema,
        validate,
    )
