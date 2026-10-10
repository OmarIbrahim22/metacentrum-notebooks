"""Unit tests for the non-dependency helpers in mcnb.util. No network."""
import subprocess

import pytest

from mcnb.util import fmt_error, run, safe_get


def test_fmt_error_with_label():
    assert fmt_error(ValueError("boom"), label="upload") == "✗ upload: ValueError: boom"


def test_fmt_error_without_label():
    assert fmt_error(KeyError("k")) == "✗ KeyError: 'k'"


def test_fmt_error_is_never_empty():
    out = fmt_error(RuntimeError())
    assert out.startswith("✗ RuntimeError: ")
    assert out != "✗ RuntimeError: "


def test_safe_get_walks_nested_dict():
    assert safe_get({"Error": {"Code": "X"}}, "Error", "Code") == "X"


def test_safe_get_default_on_missing_key_or_non_dict():
    assert safe_get({"a": 1}, "b") == "<missing>"
    assert safe_get({"a": 1}, "a", "b", default="d") == "d"
    assert safe_get(None, "a", default="d") == "d"


def test_run_returns_stdout():
    assert run("echo hi") == "hi"


def test_run_raises_on_failure_when_check_true():
    with pytest.raises(subprocess.CalledProcessError):
        run("exit 3")


def test_run_returns_stderr_on_failure_when_check_false():
    assert run("echo err >&2; exit 3", check=False) == "err"


def test_run_reports_timeout():
    assert "timed out after 1s" in run("sleep 5", timeout=1)
