"""
Full end-to-end execution of notebooks that call real external services
(S3, Invenio/NRP, OpenStack, Open WebUI) using YOUR real credentials.

NOT run by default. `pytest` alone skips this whole module. Opt in with:

    pytest -m integration

These tests use whatever credentials mcnb.env resolves (repo .env,
~/.config/mcnb/env, etc.) — the same resolution the notebooks themselves
use. A notebook is skipped (not failed) if its required env vars aren't
set, so this is safe to run without every credential configured.

Known caveat as of this writing: notebook 02 needs NRP_TOKEN; if your .env
has a duplicated NRP_BASE/NRP_TOKEN block with an empty second NRP_TOKEN=,
that later empty value wins and this test will correctly report it missing.
"""
import nbformat
import pytest
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError

from conftest import CREDENTIALED_NOTEBOOKS, NOTEBOOKS_DIR

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def _load_env():
    # Mirrors what every notebook's `from mcnb.env import ...` does on import.
    from mcnb import env as mcnb_env
    mcnb_env.reload()


@pytest.mark.parametrize("name,spec", CREDENTIALED_NOTEBOOKS.items())
def test_notebook_executes_with_real_credentials(name, spec):
    import os

    required_vars, _extra = spec
    missing = [v for v in required_vars if not os.getenv(v)]
    if missing:
        pytest.skip(f"{name}: missing credentials {missing} — configure .env to run this")

    nb = nbformat.read(NOTEBOOKS_DIR / f"{name}.ipynb", as_version=4)
    client = NotebookClient(nb, timeout=180, kernel_name="python3")
    try:
        client.execute()
    except CellExecutionError as e:
        pytest.fail(f"{name}.ipynb raised during execution against real services:\n{e}")
