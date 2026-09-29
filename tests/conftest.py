"""
Shared fixtures and constants for the notebook test suite.

Safe tests (the default `pytest` run) never touch the network and never read
or write your real ~/.config/mcnb/env or repo .env — they use an isolated
fake HOME instead. Only tests marked `integration` (opt-in via
`pytest -m integration`) use your real credentials and call real services.
"""
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
NOTEBOOKS_DIR = REPO_ROOT / "notebooks"

# Notebooks with a Python kernel (i.e. testable with ast/nbclient in this repo).
# 06 (R) and 07 (MATLAB) are excluded — they need kernels this repo doesn't install.
PY_KERNEL_NOTEBOOKS = [
    "00_environment_check",
    "01_s3_object_storage",
    "02_invenio_repository",
    "03_openstack_api",
    "04_open_webui_chat_api",
    "05_gpu_container_ai_model",
]

# Notebooks that need no external credentials — safe to execute fully.
CREDENTIAL_FREE_NOTEBOOKS = [
    "00_environment_check",
    "05_gpu_container_ai_model",
]

# notebook -> (env vars it needs, pip extra that provides its 3rd-party dep)
CREDENTIALED_NOTEBOOKS = {
    "01_s3_object_storage": (
        ["S3_ENDPOINT", "S3_ACCESS_KEY", "S3_SECRET_KEY", "S3_BUCKET"],
        "s3",
    ),
    "02_invenio_repository": (["NRP_TOKEN"], "invenio"),
    "03_openstack_api": (
        ["OS_AUTH_URL", "OS_APPLICATION_CREDENTIAL_ID", "OS_APPLICATION_CREDENTIAL_SECRET"],
        "openstack",
    ),
    "04_open_webui_chat_api": (["EINFRA_AI_TOKEN"], "openwebui"),
}


@pytest.fixture
def fake_home(tmp_path, monkeypatch):
    """
    Isolated HOME so a test can never read or write the real
    ~/.config/mcnb/env, and setup_env() never blocks on real input.
    """
    home = tmp_path / "home"
    config_dir = home / ".config" / "mcnb"
    config_dir.mkdir(parents=True)
    (config_dir / "env").write_text("MCNB_TEST_PLACEHOLDER=1\n")
    monkeypatch.setenv("HOME", str(home))
    return home
