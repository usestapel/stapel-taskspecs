"""Dataclass models for the taskspecs v1 artifacts.

Every artifact is a small dataclass with three shared affordances:

* :meth:`from_dict` — tolerant parse. Unknown keys are preserved in ``extra``
  (forward compatibility: a v1 reader must not drop or reject fields a later
  producer added), and ``schema_version`` defaults to the current major.
* :meth:`to_dict` — round-trip back to a plain JSON-able dict, re-merging
  ``extra`` and omitting empty optional fields.
* :meth:`validate` / :meth:`parse` — schema validation via
  :mod:`stapel_taskspecs.validation` (imported lazily so the dataclass path
  stays free of ``jsonschema``).

Nested collections (criteria, controls, operations, ...) are kept as plain
dicts/lists so that unknown nested fields survive a round trip untouched. The
one exception is :class:`UsageSplit`, which is a real dataclass because its
five-component shape is a load-bearing protocol condition.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, ClassVar

# Field names owned by each dataclass; anything else in the input dict lands in
# ``extra``. schema_version is handled separately (stamped, not stored in extra).
_USAGE_FIELDS = ("cache_read", "cache_write", "fresh_input", "output", "thinking")


def _split_extra(data: dict[str, Any], known: tuple[str, ...]) -> dict[str, Any]:
    """Return the subset of ``data`` whose keys are not known nor schema_version."""
    reserved = set(known) | {"schema_version"}
    return {k: v for k, v in data.items() if k not in reserved}


def _prune(d: dict[str, Any]) -> dict[str, Any]:
    """Drop keys whose value is None or an empty list/dict (keep 0 / '' / False)."""
    return {k: v for k, v in d.items() if v is not None and v != [] and v != {}}


# --------------------------------------------------------------------------
# usage split — closed, five components, the protocol condition


@dataclass
class UsageSplit:
    """Token accounting for a call, split into exactly five components.

    Deliberately closed (unlike the forward-compatible artifact envelopes):
    the split is a protocol condition. :meth:`validate` enforces the exact
    five-component, non-negative shape.
    """

    ARTIFACT: ClassVar[str] = "usage_split"

    cache_read: int = 0
    cache_write: int = 0
    fresh_input: int = 0
    output: int = 0
    thinking: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UsageSplit":
        if not isinstance(data, dict):
            raise TypeError(f"UsageSplit expects a dict, got {type(data).__name__}")
        return cls(**{k: data[k] for k in _USAGE_FIELDS if k in data})

    def to_dict(self) -> dict[str, Any]:
        return {k: getattr(self, k) for k in _USAGE_FIELDS}

    def validate(self) -> "UsageSplit":
        from .validation import validate

        validate(self.to_dict(), self.ARTIFACT)
        return self

    @property
    def prompt_tokens(self) -> int:
        """Total prompt-side tokens (cache_read + cache_write + fresh_input)."""
        return self.cache_read + self.cache_write + self.fresh_input

    @property
    def total_tokens(self) -> int:
        """Sum of all five components."""
        return sum(getattr(self, k) for k in _USAGE_FIELDS)


# --------------------------------------------------------------------------
# artifact envelopes — forward-compatible


class _Artifact:
    """Mixin providing validate()/parse() over a subclass ``to_dict``."""

    ARTIFACT: ClassVar[str]

    def to_dict(self) -> dict[str, Any]:  # pragma: no cover - overridden
        raise NotImplementedError

    def validate(self):
        from .validation import validate

        validate(self.to_dict(), self.ARTIFACT)
        return self

    @classmethod
    def parse(cls, data: dict[str, Any], *, validate: bool = True):
        """from_dict + (optionally) schema validation in one call."""
        obj = cls.from_dict(data)  # type: ignore[attr-defined]
        if validate:
            obj.validate()
        return obj


@dataclass
class TaskSpec(_Artifact):
    ARTIFACT: ClassVar[str] = "task_spec"
    _KNOWN: ClassVar[tuple[str, ...]] = (
        "id", "type", "goal", "status", "risk", "spec_refs", "depends_on",
        "criteria", "out_of_scope", "budget", "body",
    )

    id: str = ""
    type: str = ""
    goal: str = ""
    criteria: list[dict[str, Any]] = field(default_factory=list)
    budget: dict[str, Any] = field(default_factory=dict)
    status: str | None = None
    risk: list[str] = field(default_factory=list)
    spec_refs: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
    out_of_scope: list[str] = field(default_factory=list)
    body: str | None = None
    schema_version: int = 1
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskSpec":
        return cls(
            id=data.get("id", ""),
            type=data.get("type", ""),
            goal=data.get("goal", ""),
            criteria=data.get("criteria", []) or [],
            budget=data.get("budget", {}) or {},
            status=data.get("status"),
            risk=data.get("risk", []) or [],
            spec_refs=data.get("spec_refs", []) or [],
            depends_on=data.get("depends_on", []) or [],
            out_of_scope=data.get("out_of_scope", []) or [],
            body=data.get("body"),
            schema_version=data.get("schema_version", 1),
            extra=_split_extra(data, cls._KNOWN),
        )

    def to_dict(self) -> dict[str, Any]:
        out = {
            "schema_version": self.schema_version,
            "id": self.id,
            "type": self.type,
            "goal": self.goal,
            "status": self.status,
            "risk": self.risk,
            "spec_refs": self.spec_refs,
            "depends_on": self.depends_on,
            "criteria": self.criteria,
            "out_of_scope": self.out_of_scope,
            "budget": self.budget,
            "body": self.body,
        }
        return {**_prune(out), **self.extra}


@dataclass
class TaskReport(_Artifact):
    ARTIFACT: ClassVar[str] = "task_report"
    _KNOWN: ClassVar[tuple[str, ...]] = (
        "task_id", "status", "summary_business", "files_changed", "controls",
        "commits", "questions", "failure_type", "iterations", "usage",
    )

    task_id: str = ""
    status: str = ""
    usage: UsageSplit = field(default_factory=UsageSplit)
    summary_business: str | None = None
    files_changed: list[str] = field(default_factory=list)
    controls: dict[str, Any] = field(default_factory=dict)
    commits: list[str] = field(default_factory=list)
    questions: list[str] = field(default_factory=list)
    failure_type: str | None = None
    iterations: int | None = None
    schema_version: int = 1
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskReport":
        raw_usage = data.get("usage")
        usage = UsageSplit.from_dict(raw_usage) if isinstance(raw_usage, dict) else UsageSplit()
        return cls(
            task_id=data.get("task_id", ""),
            status=data.get("status", ""),
            usage=usage,
            summary_business=data.get("summary_business"),
            files_changed=data.get("files_changed", []) or [],
            controls=data.get("controls", {}) or {},
            commits=data.get("commits", []) or [],
            questions=data.get("questions", []) or [],
            failure_type=data.get("failure_type"),
            iterations=data.get("iterations"),
            schema_version=data.get("schema_version", 1),
            extra=_split_extra(data, cls._KNOWN),
        )

    def to_dict(self) -> dict[str, Any]:
        out = {
            "schema_version": self.schema_version,
            "task_id": self.task_id,
            "status": self.status,
            "summary_business": self.summary_business,
            "files_changed": self.files_changed,
            "controls": self.controls,
            "commits": self.commits,
            "questions": self.questions,
            "failure_type": self.failure_type,
            "iterations": self.iterations,
        }
        # usage is always present (protocol condition) and never pruned.
        return {**_prune(out), "usage": self.usage.to_dict(), **self.extra}


@dataclass
class SpecPatch(_Artifact):
    ARTIFACT: ClassVar[str] = "spec_patch"
    _KNOWN: ClassVar[tuple[str, ...]] = ("operations", "confirmation_text")

    operations: list[dict[str, Any]] = field(default_factory=list)
    confirmation_text: str | None = None
    schema_version: int = 1
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SpecPatch":
        return cls(
            operations=data.get("operations", []) or [],
            confirmation_text=data.get("confirmation_text"),
            schema_version=data.get("schema_version", 1),
            extra=_split_extra(data, cls._KNOWN),
        )

    def to_dict(self) -> dict[str, Any]:
        out = {
            "schema_version": self.schema_version,
            "operations": self.operations,
            "confirmation_text": self.confirmation_text,
        }
        # operations kept even if empty would fail schema (minItems 1); prune
        # empties so an invalid instance surfaces via validation, not silently.
        return {**_prune(out), **self.extra}


@dataclass
class QAReport(_Artifact):
    ARTIFACT: ClassVar[str] = "qa_report"
    _KNOWN: ClassVar[tuple[str, ...]] = ("task_id", "criteria_results")

    task_id: str = ""
    criteria_results: list[dict[str, Any]] = field(default_factory=list)
    schema_version: int = 1
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "QAReport":
        return cls(
            task_id=data.get("task_id", ""),
            criteria_results=data.get("criteria_results", []) or [],
            schema_version=data.get("schema_version", 1),
            extra=_split_extra(data, cls._KNOWN),
        )

    def to_dict(self) -> dict[str, Any]:
        out = {
            "schema_version": self.schema_version,
            "task_id": self.task_id,
            "criteria_results": self.criteria_results,
        }
        return {**out, **self.extra}


@dataclass
class EscalationQuestion(_Artifact):
    ARTIFACT: ClassVar[str] = "escalation_question"
    _KNOWN: ClassVar[tuple[str, ...]] = ("task_id", "question", "options")

    task_id: str = ""
    question: str = ""
    options: list[str] = field(default_factory=list)
    schema_version: int = 1
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EscalationQuestion":
        return cls(
            task_id=data.get("task_id", ""),
            question=data.get("question", ""),
            options=data.get("options", []) or [],
            schema_version=data.get("schema_version", 1),
            extra=_split_extra(data, cls._KNOWN),
        )

    def to_dict(self) -> dict[str, Any]:
        out = {
            "schema_version": self.schema_version,
            "task_id": self.task_id,
            "question": self.question,
            "options": self.options,
        }
        return {**_prune(out), **self.extra}


@dataclass
class ReviewFinding(_Artifact):
    ARTIFACT: ClassVar[str] = "review_finding"
    _KNOWN: ClassVar[tuple[str, ...]] = (
        "fingerprint", "claim", "severity", "category", "location",
        "repro_test_path", "repro_test", "count", "status",
    )

    fingerprint: str = ""
    claim: str = ""
    severity: str = ""
    category: str | None = None
    location: str | None = None
    repro_test_path: str | None = None
    repro_test: str | None = None
    count: int | None = None
    status: str | None = None
    schema_version: int = 1
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReviewFinding":
        return cls(
            fingerprint=data.get("fingerprint", ""),
            claim=data.get("claim", ""),
            severity=data.get("severity", ""),
            category=data.get("category"),
            location=data.get("location"),
            repro_test_path=data.get("repro_test_path"),
            repro_test=data.get("repro_test"),
            count=data.get("count"),
            status=data.get("status"),
            schema_version=data.get("schema_version", 1),
            extra=_split_extra(data, cls._KNOWN),
        )

    def to_dict(self) -> dict[str, Any]:
        out = {
            "schema_version": self.schema_version,
            "fingerprint": self.fingerprint,
            "claim": self.claim,
            "severity": self.severity,
            "category": self.category,
            "location": self.location,
            "repro_test_path": self.repro_test_path,
            "repro_test": self.repro_test,
            "count": self.count,
            "status": self.status,
        }
        return {**_prune(out), **self.extra}


#: artifact name -> model class
MODELS: dict[str, type] = {
    TaskSpec.ARTIFACT: TaskSpec,
    TaskReport.ARTIFACT: TaskReport,
    SpecPatch.ARTIFACT: SpecPatch,
    QAReport.ARTIFACT: QAReport,
    EscalationQuestion.ARTIFACT: EscalationQuestion,
    ReviewFinding.ARTIFACT: ReviewFinding,
    UsageSplit.ARTIFACT: UsageSplit,
}
