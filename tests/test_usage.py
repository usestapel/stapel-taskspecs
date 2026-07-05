"""The five-component usage split is closed and strictly validated."""

from __future__ import annotations

import pytest

from stapel_taskspecs import UsageSplit, validate
from stapel_taskspecs.errors import SchemaValidationError

FIVE = ("cache_read", "cache_write", "fresh_input", "output", "thinking")


def test_exactly_five_components(usage_split):
    assert set(usage_split) == set(FIVE)
    validate(usage_split, "usage_split")


@pytest.mark.parametrize("missing", FIVE)
def test_missing_component_rejected(usage_split, missing):
    usage_split.pop(missing)
    with pytest.raises(SchemaValidationError):
        validate(usage_split, "usage_split")


def test_extra_component_rejected(usage_split):
    usage_split["reasoning"] = 5  # closed object: no sixth key
    with pytest.raises(SchemaValidationError):
        validate(usage_split, "usage_split")


def test_negative_rejected(usage_split):
    usage_split["output"] = -1
    with pytest.raises(SchemaValidationError):
        validate(usage_split, "usage_split")


def test_non_integer_rejected(usage_split):
    usage_split["output"] = 1.5
    with pytest.raises(SchemaValidationError):
        validate(usage_split, "usage_split")


def test_dataclass_roundtrip_and_totals(usage_split):
    u = UsageSplit.from_dict(usage_split)
    assert u.to_dict() == usage_split
    u.validate()
    assert u.prompt_tokens == u.cache_read + u.cache_write + u.fresh_input
    assert u.total_tokens == sum(usage_split.values())


def test_dataclass_defaults_to_zeros():
    u = UsageSplit()
    assert u.to_dict() == dict.fromkeys(FIVE, 0)
    u.validate()
