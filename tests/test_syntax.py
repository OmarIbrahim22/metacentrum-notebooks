"""Static checks — no execution, no network, no credentials."""
import ast

import pytest

from conftest import NOTEBOOKS_DIR, PY_KERNEL_NOTEBOOKS


@pytest.mark.parametrize("name", PY_KERNEL_NOTEBOOKS)
def test_py_source_is_valid_python(name):
    """The jupytext .py pairing must always be syntactically valid Python."""
    source = (NOTEBOOKS_DIR / f"{name}.py").read_text()
    ast.parse(source, filename=f"{name}.py")


@pytest.mark.parametrize("name", PY_KERNEL_NOTEBOOKS)
def test_no_runtime_pip_install(name):
    """
    Regression guard: notebooks must never shell out to pip on their own.

    This is the exact bug class we removed (silent `pip install --user`
    calls that break inside a venv and are opaque to reviewers). Dependency
    cells should only *check* importability via importlib.util.find_spec.
    """
    source = (NOTEBOOKS_DIR / f"{name}.py").read_text()
    assert "check_call" not in source, (
        f"{name}.py appears to shell out to install packages at runtime"
    )
    assert "--user" not in source, (
        f"{name}.py still references a --user pip install"
    )
    assert "importlib" in source and "find_spec" in source, (
        f"{name}.py should use importlib.util.find_spec for its dependency check"
    )
