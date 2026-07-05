"""Markdown + YAML front matter <-> JSON conversion."""

from __future__ import annotations

import pytest

from stapel_taskspecs import (
    TaskSpec,
    has_front_matter,
    join_front_matter,
    split_front_matter,
    taskspec_from_markdown,
    taskspec_to_markdown,
)
from stapel_taskspecs.errors import FrontMatterError

# A TaskSpec markdown projection with Cyrillic prose (round-trip must be
# unicode-clean), mirroring the slice TASKS/*.md structure.
SPEC_MD = """---
schema_version: 1
id: T-042
type: feature
goal: Клиенты салона — базовый справочник
status: DRAFT
risk:
  - validation
criteria:
  - id: C1
    text: "Дано: пустая база; Когда: POST; Тогда: 201"
budget:
  iterations: 3
  wall_min: 20
---

# Клиенты салона

Салон ведёт справочник клиентов.
"""


def test_has_front_matter():
    assert has_front_matter(SPEC_MD)
    assert not has_front_matter("# just a heading\n")


def test_split_front_matter():
    front, body = split_front_matter(SPEC_MD)
    assert front["id"] == "T-042"
    assert front["risk"] == ["validation"]
    assert body.startswith("# Клиенты салона")


def test_split_requires_fence():
    with pytest.raises(FrontMatterError):
        split_front_matter("no front matter here")


def test_taskspec_from_markdown():
    spec = taskspec_from_markdown(SPEC_MD)
    assert isinstance(spec, TaskSpec)
    assert spec.id == "T-042"
    assert spec.criteria[0]["id"] == "C1"
    assert spec.body.startswith("# Клиенты салона")


def test_taskspec_markdown_roundtrip():
    spec = taskspec_from_markdown(SPEC_MD)
    rendered = taskspec_to_markdown(spec)
    # re-parsing the rendered projection yields an equivalent spec
    spec2 = taskspec_from_markdown(rendered)
    assert spec2.to_dict() == spec.to_dict()
    # header ordering: id appears before body prose, unicode preserved
    assert "id: T-042" in rendered
    assert "Клиенты салона" in rendered


def test_join_front_matter_orders_keys():
    doc = join_front_matter({"budget": {"iterations": 1}, "id": "T-1", "goal": "g"})
    # id is rendered before budget per the preferred order
    assert doc.index("id:") < doc.index("budget:")


def test_dict_json_bridge():
    # front matter round-trips a plain dict without a body
    front = {"schema_version": 1, "id": "T-7", "type": "bug"}
    doc = join_front_matter(front, "")
    back, body = split_front_matter(doc)
    assert back == front
    assert body == ""
