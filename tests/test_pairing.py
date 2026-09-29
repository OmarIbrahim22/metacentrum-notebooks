"""
Guard against .py/.ipynb drift — no execution, no network.

These two files are a jupytext pair and must always be re-synced together
(`jupytext --sync notebooks/<name>.py`) after editing either one. This test
would have caught the exact regression hit during development: editing the
.py and forgetting to resync left the .ipynb out of date.
"""
import jupytext
import nbformat
import pytest

from conftest import NOTEBOOKS_DIR, PY_KERNEL_NOTEBOOKS


def _code_sources(nb):
    return [cell.source for cell in nb.cells if cell.cell_type == "code"]


@pytest.mark.parametrize("name", PY_KERNEL_NOTEBOOKS)
def test_ipynb_matches_py_pairing(name):
    py_nb = jupytext.read(NOTEBOOKS_DIR / f"{name}.py")
    ipynb_nb = nbformat.read(NOTEBOOKS_DIR / f"{name}.ipynb", as_version=4)

    assert _code_sources(py_nb) == _code_sources(ipynb_nb), (
        f"{name}.py and {name}.ipynb code cells have drifted apart — "
        f"run: jupytext --sync notebooks/{name}.py"
    )
