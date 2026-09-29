"""
Unit tests for mcnb.util.check_deps / require_deps — the shared helper behind
every notebook's dependency-check cell. No network, no subprocess, no venvs:
missing packages are simulated with fake module names instead of actually
uninstalling anything.
"""
import pytest

from mcnb.util import check_deps, require_deps


def test_check_deps_reports_nothing_missing_when_all_present():
    assert check_deps({"python-dotenv": "dotenv"}) == []


def test_check_deps_reports_missing_package():
    missing = check_deps({"definitely-not-a-real-package": "definitely_not_a_real_module"})
    assert missing == ["definitely-not-a-real-package"]


def test_check_deps_reports_only_the_missing_ones():
    missing = check_deps(
        {
            "python-dotenv": "dotenv",
            "definitely-not-a-real-package": "definitely_not_a_real_module",
        }
    )
    assert missing == ["definitely-not-a-real-package"]


def test_require_deps_passes_silently_when_satisfied():
    require_deps({"python-dotenv": "dotenv"})  # must not raise


def test_require_deps_raises_importerror_with_install_command():
    with pytest.raises(ImportError) as exc_info:
        require_deps(
            {"definitely-not-a-real-package": "definitely_not_a_real_module"},
            extra="s3",
        )
    message = str(exc_info.value)
    assert "definitely-not-a-real-package" in message
    assert 'pip install -e ".[s3]"' in message


def test_require_deps_without_extra_suggests_base_install():
    with pytest.raises(ImportError) as exc_info:
        require_deps({"definitely-not-a-real-package": "definitely_not_a_real_module"})
    assert "pip install -e ." in str(exc_info.value)


def test_require_deps_never_installs_anything(monkeypatch):
    """Guard against reintroducing a subprocess-based auto-install."""
    def _fail_if_called(*args, **kwargs):
        raise AssertionError("require_deps must never invoke subprocess")

    monkeypatch.setattr("subprocess.check_call", _fail_if_called)
    monkeypatch.setattr("subprocess.run", _fail_if_called)

    with pytest.raises(ImportError):
        require_deps({"definitely-not-a-real-package": "definitely_not_a_real_module"})
