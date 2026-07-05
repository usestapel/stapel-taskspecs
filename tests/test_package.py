"""Package-level contracts: lazy import stays light; __all__ resolves."""

from __future__ import annotations

import subprocess
import sys

import stapel_taskspecs


def test_all_names_resolve():
    for name in stapel_taskspecs.__all__:
        assert getattr(stapel_taskspecs, name) is not None


def test_unknown_attribute_raises():
    import pytest

    with pytest.raises(AttributeError):
        stapel_taskspecs.does_not_exist


def test_bare_import_does_not_pull_jsonschema():
    # PEP 562 laziness: importing the package must not import jsonschema until
    # a validation symbol is actually touched.
    code = (
        "import sys; import stapel_taskspecs; "
        "assert 'jsonschema' not in sys.modules, sorted(m for m in sys.modules if 'json' in m)"
    )
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_version_exposed():
    assert stapel_taskspecs.__version__ == "0.1.0"
