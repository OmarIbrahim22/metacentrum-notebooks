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


@pytest.mark.parametrize("path", sorted(NOTEBOOKS_DIR.glob("*.ipynb")), ids=lambda p: p.stem)
def test_notebook_has_no_outputs(path):
    """
    Notebooks are committed clean: no outputs, no execution counts.

    Outputs leak local paths and account details, and make every re-run
    show up as a diff.
    """
    import nbformat

    nb = nbformat.read(path, as_version=4)
    dirty = [
        i for i, cell in enumerate(nb.cells)
        if cell.cell_type == "code" and (cell.outputs or cell.execution_count is not None)
    ]
    assert not dirty, (
        f"{path.name} has outputs in cells {dirty} — clear all outputs before committing"
    )
