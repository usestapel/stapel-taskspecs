"""Dataclass models: tolerant parse, round trip, forward-compat, validation."""

from __future__ import annotations

import pytest

from stapel_taskspecs import (
    MODELS,
    EscalationQuestion,
    QAReport,
    ReviewFinding,
    SpecPatch,
    TaskReport,
    TaskSpec,
)
from stapel_taskspecs.errors import SchemaValidationError

CASES = [
    ("task_spec", TaskSpec),
    ("task_report", TaskReport),
    ("spec_patch", SpecPatch),
    ("qa_report", QAReport),
    ("escalation_question", EscalationQuestion),
    ("review_finding", ReviewFinding),
]


@pytest.fixture
def sample(request):
    return request.getfixturevalue(request.param)


@pytest.mark.parametrize("fixture_name, model", CASES)
def test_parse_and_validate(fixture_name, model, request):
    data = request.getfixturevalue(fixture_name)
    obj = model.parse(data, validate=True)
    assert isinstance(obj, model)


@pytest.mark.parametrize("fixture_name, model", CASES)
def test_roundtrip_preserves_payload(fixture_name, model, request):
    data = request.getfixturevalue(fixture_name)
    obj = model.from_dict(data)
    out = obj.to_dict()
    # every non-empty original value survives verbatim; empty optional
    # collections may be pruned (absent == empty, lossless), so re-parsing the
    # emitted dict must reproduce an identical model.
    for key, value in data.items():
        if value in ([], {}, None):
            continue
        assert out[key] == value, key
    assert model.from_dict(out).to_dict() == out


@pytest.mark.parametrize("fixture_name, model", CASES)
def test_forward_compat_unknown_fields_preserved(fixture_name, model, request):
    data = request.getfixturevalue(fixture_name)
    data["future_field"] = {"nested": [1, 2]}
    obj = model.from_dict(data)
    assert obj.extra["future_field"] == {"nested": [1, 2]}
    # round trip re-emits it and still validates (schemas are open)
    assert obj.to_dict()["future_field"] == {"nested": [1, 2]}
    obj.validate()


def test_schema_version_stamped_when_absent():
    obj = TaskSpec.from_dict(
        {"id": "T-1", "type": "feature", "goal": "g", "criteria": [], "budget": {"iterations": 1}}
    )
    assert obj.schema_version == 1
    assert obj.to_dict()["schema_version"] == 1


def test_task_report_usage_is_dataclass_and_always_emitted():
    obj = TaskReport.from_dict({"task_id": "T-1", "status": "failed"})
    assert obj.usage.to_dict() == {
        "cache_read": 0, "cache_write": 0, "fresh_input": 0, "output": 0, "thinking": 0,
    }
    # usage present even for a failed report (protocol condition)
    assert "usage" in obj.to_dict()
    obj.validate()


def test_invalid_instance_fails_validation():
    obj = TaskSpec.from_dict({"id": "", "type": "feature", "goal": "g"})
    with pytest.raises(SchemaValidationError):
        obj.validate()


def test_parse_can_skip_validation():
    # validate=False lets an incomplete draft through the dataclass
    obj = SpecPatch.parse({"operations": []}, validate=False)
    assert obj.operations == []


def test_models_registry_complete():
    assert set(MODELS) >= {n for n, _ in CASES} | {"usage_split"}
