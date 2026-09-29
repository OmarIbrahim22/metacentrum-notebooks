"""Cross-check notebook install instructions against pyproject.toml extras."""
import sys

import pytest

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # noqa: F401 (only needed on very old Python)

from conftest import CREDENTIALED_NOTEBOOKS, NOTEBOOKS_DIR, REPO_ROOT


@pytest.fixture(scope="module")
def declared_extras():
    with open(REPO_ROOT / "pyproject.toml", "rb") as fh:
        data = tomllib.load(fh)
    return set(data["project"]["optional-dependencies"])


@pytest.mark.parametrize("name,spec", CREDENTIALED_NOTEBOOKS.items())
def test_notebook_extra_is_declared_in_pyproject(name, spec, declared_extras):
    _, extra = spec
    assert extra in declared_extras, (
        f"{name}.py references extra '{extra}' which is missing from "
        f"pyproject.toml [project.optional-dependencies]"
    )


@pytest.mark.parametrize("name,spec", CREDENTIALED_NOTEBOOKS.items())
def test_notebook_advertises_its_own_extra(name, spec):
    """The notebook's install instructions must point at the right extra."""
    _, extra = spec
    source = (NOTEBOOKS_DIR / f"{name}.py").read_text()
    assert f'.[{extra}]' in source, (
        f"{name}.py doesn't mention 'pip install -e \".[{extra}]\"' anywhere"
    )
