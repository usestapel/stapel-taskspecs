"""Exception types for stapel-taskspecs.

Django-free, stdlib-only. Kept in their own module so callers can catch the
package's error taxonomy without importing jsonschema.
"""

from __future__ import annotations


class TaskSpecsError(Exception):
    """Base class for every error raised by stapel-taskspecs."""


class SchemaValidationError(TaskSpecsError):
    """An artifact instance did not validate against its JSON Schema.

    ``errors`` holds one human-readable line per validation failure (best
    effort — populated when validation was run through :mod:`stapel_taskspecs.
    validation`).
    """

    def __init__(self, message: str, errors: list[str] | None = None) -> None:
        super().__init__(message)
        self.errors: list[str] = errors or []


class FrontMatterError(TaskSpecsError):
    """A markdown document could not be split into YAML front matter + body."""


class UnknownArtifactError(TaskSpecsError):
    """No schema is registered under the requested artifact name."""
