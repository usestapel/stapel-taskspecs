"""Shared valid-sample fixtures for the taskspecs artifacts.

Samples mirror the *structure* of real slice artifacts (fields, types, states)
without carrying any pipeline prose/rules — enough to exercise the schemas.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def usage_split() -> dict:
    return {
        "cache_read": 18000,
        "cache_write": 0,
        "fresh_input": 320,
        "output": 640,
        "thinking": 0,
    }


@pytest.fixture
def task_spec() -> dict:
    return {
        "schema_version": 1,
        "id": "T-001",
        "type": "feature",
        "goal": "CRUD entity: list, create, view and edit",
        "status": "DRAFT",
        "risk": ["validation"],
        "spec_refs": ["domain.entity", "story.S-01"],
        "depends_on": [],
        "criteria": [
            {"id": "C1", "text": "Given: empty db; When: POST; Then: 201"},
            {"id": "C2", "text": "Given: created; When: GET list; Then: present"},
        ],
        "out_of_scope": ["UI form"],
        "budget": {"iterations": 3, "tokens_m": 1, "wall_min": 20},
        "body": "# Prose body\n\nHuman-readable context.",
    }


@pytest.fixture
def task_report(usage_split) -> dict:
    return {
        "schema_version": 1,
        "task_id": "T-001",
        "status": "done",
        "summary_business": "Entity CRUD is live.",
        "files_changed": ["apps/x/models.py", "apps/x/views.py"],
        "controls": {
            "lint": {"status": "pass"},
            "types": {"status": "pass"},
            "tests": {"status": "pass", "log": "12 passed"},
        },
        "commits": ["abc1234"],
        "questions": [],
        "iterations": 2,
        "usage": usage_split,
    }


@pytest.fixture
def spec_patch() -> dict:
    return {
        "schema_version": 1,
        "operations": [
            {"op": "add_story", "target": "S-02", "payload": {"title": "Login"}},
            {"op": "update_status", "target": "S-01", "payload": "live"},
        ],
        "confirmation_text": "I will add a login story and mark S-01 done.",
    }


@pytest.fixture
def qa_report() -> dict:
    return {
        "schema_version": 1,
        "task_id": "T-001",
        "criteria_results": [
            {"criterion_id": "C1", "status": "pass"},
            {
                "criterion_id": "C2",
                "status": "fail",
                "screenshot_ref": "runs/T-001/shot.png",
                "repro_steps": "open list, item missing",
            },
        ],
    }


@pytest.fixture
def escalation_question() -> dict:
    return {
        "schema_version": 1,
        "task_id": "T-009",
        "question": "How many reminders should we send, and on what channel?",
        "options": ["One, by email", "Two, by SMS"],
    }


@pytest.fixture
def review_finding() -> dict:
    return {
        "schema_version": 1,
        "fingerprint": "validation:apps/x/serializers.py:phone-uniqueness",
        "claim": "duplicate phone is accepted where it must 400",
        "severity": "blocker",
        "category": "validation",
        "location": "apps/x/serializers.py:42",
        "repro_test_path": "tests/review/test_dup_phone.py",
        "count": 1,
        "status": "open",
    }
