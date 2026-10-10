"""
Full end-to-end execution of the notebooks that need no external credentials.

Safe by construction: 00 and 05 never call an external service (00 is local
diagnostics, 05 degrades gracefully with no GPU/container runtime). HOME is
redirected to an isolated temp dir so the credential-wizard cell in 00 finds
a pre-seeded ~/.config/mcnb/env and skips interactive prompts, and nothing
touches your real ~/.config. A repo-root .env, if present, is still loaded
by mcnb.env inside the kernel (only HOME is faked); these notebooks never
send it anywhere.
"""
import nbformat
import pytest
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError

from conftest import CREDENTIAL_FREE_NOTEBOOKS, NOTEBOOKS_DIR


@pytest.mark.parametrize("name", CREDENTIAL_FREE_NOTEBOOKS)
def test_notebook_executes_without_error(name, fake_home):
    nb = nbformat.read(NOTEBOOKS_DIR / f"{name}.ipynb", as_version=4)
    client = NotebookClient(nb, timeout=120, kernel_name="python3")
    try:
        client.execute()
    except CellExecutionError as e:
        pytest.fail(f"{name}.ipynb raised during execution:\n{e}")
