"""Markdown + YAML front matter <-> JSON conversion.

The repository projection of a task is markdown with a YAML front-matter block
(machine fields in the header, human prose in the body); the canonical form
inside the pipeline is JSON validated by schema (system-design 7.17). This
module is the bridge between the two.

Dependency note: front matter is a trivial ``---\\n<yaml>\\n---\\n<body>``
envelope, so we split it with the stdlib and parse the YAML block with PyYAML
(already required, since the header is YAML). We deliberately do NOT pull in
``python-frontmatter``: it would be a whole dependency for a ten-line split,
and it hardcodes its own metadata handling we do not want.
"""

from __future__ import annotations

import re
from typing import Any

import yaml

from .errors import FrontMatterError

_FRONT_MATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?(.*)\Z", re.S)

# Preferred key order when rendering a TaskSpec header (readability; unlisted
# keys follow in insertion order).
_TASKSPEC_KEY_ORDER = (
    "schema_version", "id", "type", "goal", "status", "risk", "spec_refs",
    "depends_on", "criteria", "out_of_scope", "budget",
)


def has_front_matter(text: str) -> bool:
    """True if ``text`` opens with a ``---`` YAML front-matter fence."""
    return bool(_FRONT_MATTER_RE.match(text))


def split_front_matter(text: str) -> tuple[dict[str, Any], str]:
    """Split a markdown document into (front-matter mapping, body).

    Raises :class:`FrontMatterError` if there is no front-matter fence or the
    YAML block is not a mapping.
    """
    m = _FRONT_MATTER_RE.match(text)
    if not m:
        raise FrontMatterError("document has no YAML front-matter block")
    try:
        front = yaml.safe_load(m.group(1))
    except yaml.YAMLError as exc:
        raise FrontMatterError(f"invalid YAML front matter: {exc}") from exc
    if front is None:
        front = {}
    if not isinstance(front, dict):
        raise FrontMatterError("front matter must be a mapping")
    return front, m.group(2).strip()


def join_front_matter(front: dict[str, Any], body: str = "") -> str:
    """Render a (front-matter mapping, body) pair back to a markdown document."""
    header = yaml.safe_dump(
        _as_ordered(front),
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    ).rstrip("\n")
    body = (body or "").strip()
    doc = f"---\n{header}\n---\n"
    if body:
        doc += f"\n{body}\n"
    return doc


def _as_ordered(front: dict[str, Any]) -> dict[str, Any]:
    # A plain dict preserves insertion order (3.7+) and stays representable by
    # PyYAML's SafeDumper (which refuses OrderedDict).
    ordered: dict[str, Any] = {}
    for key in _TASKSPEC_KEY_ORDER:
        if key in front:
            ordered[key] = front[key]
    for key, value in front.items():
        if key not in ordered:
            ordered[key] = value
    return ordered


# --------------------------------------------------------------------------
# TaskSpec-specific helpers (TaskSpec is the artifact with a prose body)


def taskspec_from_markdown(text: str, *, validate: bool = True):
    """Parse a TaskSpec markdown projection into a :class:`TaskSpec`.

    The body below the front matter is carried in ``TaskSpec.body``.
    """
    from .models import TaskSpec

    front, body = split_front_matter(text)
    data = dict(front)
    if body:
        data["body"] = body
    data.setdefault("schema_version", 1)
    return TaskSpec.parse(data, validate=validate)


def taskspec_to_markdown(spec, *, validate: bool = True) -> str:
    """Render a :class:`TaskSpec` back to its markdown projection.

    Machine fields become the YAML header; ``spec.body`` becomes the prose.
    """
    if validate:
        spec.validate()
    data = spec.to_dict()
    body = data.pop("body", "") or ""
    return join_front_matter(data, body)
