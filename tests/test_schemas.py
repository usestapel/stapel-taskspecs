"""JSON Schema surface: every schema is well-formed, samples validate, the
cross-file usage $ref resolves, and invalid instances are rejected."""

from __future__ import annotations

import pytest
from jsonschema import Draft202012Validator

from stapel_taskspecs import validation
from stapel_taskspecs.errors import SchemaValidationError, UnknownArtifactError

ARTIFACTS = [
    "task_spec",
    "task_report",
    "spec_patch",
    "qa_report",
    "escalation_question",
    "review_finding",
    "usage_split",
]


def test_all_artifacts_registered():
    assert set(validation.artifact_names()) == set(ARTIFACTS)


@pytest.mark.parametrize("name", ARTIFACTS)
def test_schema_is_well_formed(name):
    schema = validation.load_schema(name)
    Draft202012Validator.check_schema(schema)
    assert schema["$id"].endswith(f"{name}.v1.json")


def test_valid_samples_pass(
    task_spec, task_report, spec_patch, qa_report, escalation_question, review_finding, usage_split
):
    validation.validate(task_spec, "task_spec")
    validation.validate(task_report, "task_report")
    validation.validate(spec_patch, "spec_patch")
    validation.validate(qa_report, "qa_report")
    validation.validate(escalation_question, "escalation_question")
    validation.validate(review_finding, "review_finding")
    validation.validate(usage_split, "usage_split")


def test_task_report_usage_ref_resolves(task_report):
    # A broken usage sub-object must surface via the $ref to usage_split.
    task_report["usage"].pop("thinking")
    assert not validation.is_valid(task_report, "task_report")
    errors = validation.iter_errors(task_report, "task_report")
    assert any("thinking" in e for e in errors)


def test_validate_raises_with_error_lines():
    with pytest.raises(SchemaValidationError) as exc:
        validation.validate({"schema_version": 1}, "task_spec")
    assert exc.value.errors  # required-field failures collected


def test_unknown_artifact():
    with pytest.raises(UnknownArtifactError):
        validation.load_schema("nope")


def test_schema_version_const_enforced(task_spec):
    task_spec["schema_version"] = 2
    assert not validation.is_valid(task_spec, "task_spec")


def test_forward_compat_unknown_top_level_field_ok(task_spec):
    task_spec["some_future_field"] = {"a": 1}
    validation.validate(task_spec, "task_spec")  # must not reject
