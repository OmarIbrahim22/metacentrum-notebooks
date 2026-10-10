"""
Unit tests for mcnb.env: file discovery order, the stdlib fallback loader,
need()/optional()/mask(). No network. HOME is redirected by `fake_home`;
env files are written to tmp_path, never to the real repo root.
"""
import pytest

from mcnb import env


def test_env_files_priority_order(tmp_path, fake_home):
    (tmp_path / "env_b").write_text("A=1\n")
    (tmp_path / "env_a").write_text("A=1\n")
    (tmp_path / "env").write_text("A=1\n")
    (tmp_path / ".env").write_text("A=1\n")
    (tmp_path / "env.example").write_text("A=REPLACE_ME\n")
    (tmp_path / "env_x.example").write_text("A=REPLACE_ME\n")
    files = env._env_files(tmp_path)
    assert [p.name for p in files[:-1]] == ["env_a", "env_b", "env", ".env"]
    assert files[-1] == fake_home / ".config" / "mcnb" / "env"


def test_stdlib_fallback_parses_comments_and_quotes(tmp_path, monkeypatch):
    monkeypatch.setattr(env, "_HAS_DOTENV", False)
    monkeypatch.setenv("MCNB_T_PLAIN", "old")  # registers cleanup
    monkeypatch.setenv("MCNB_T_QUOTED", "old")
    monkeypatch.setenv("MCNB_T_SINGLE", "old")
    f = tmp_path / "envfile"
    f.write_text(
        "# comment\n\nnot a pair\n"
        "MCNB_T_PLAIN=abc\n"
        'MCNB_T_QUOTED="q v"\n'
        "MCNB_T_SINGLE='s'\n"
    )
    env._load_file(f)
    assert env.optional("MCNB_T_PLAIN") == "abc"
    assert env.optional("MCNB_T_QUOTED") == "q v"
    assert env.optional("MCNB_T_SINGLE") == "s"


def test_file_value_overrides_existing_environment(tmp_path, monkeypatch):
    """Documents current behaviour: env files win over exported variables."""
    monkeypatch.setattr(env, "_HAS_DOTENV", False)
    monkeypatch.setenv("MCNB_T_OVR", "from-shell")
    f = tmp_path / "envfile"
    f.write_text("MCNB_T_OVR=from-file\n")
    env._load_file(f)
    assert env.optional("MCNB_T_OVR") == "from-file"


def test_need_returns_value(monkeypatch):
    monkeypatch.setenv("MCNB_T_NEED", "secret")
    assert env.need("MCNB_T_NEED") == "secret"


def test_need_raises_with_name_when_missing(monkeypatch):
    monkeypatch.setattr(env, "_env_files", lambda root: [])
    monkeypatch.setenv("MCNB_T_MISSING", "")  # empty counts as missing
    with pytest.raises(RuntimeError) as exc_info:
        env.need("MCNB_T_MISSING")
    assert "MCNB_T_MISSING" in str(exc_info.value)


def test_need_reloads_files_once_before_failing(tmp_path, monkeypatch):
    monkeypatch.setattr(env, "_HAS_DOTENV", False)
    monkeypatch.setenv("MCNB_T_LATE", "")
    f = tmp_path / "envfile"
    f.write_text("MCNB_T_LATE=found\n")
    monkeypatch.setattr(env, "_env_files", lambda root: [f])
    assert env.need("MCNB_T_LATE") == "found"


def test_optional_default(monkeypatch):
    monkeypatch.delenv("MCNB_T_OPT", raising=False)
    assert env.optional("MCNB_T_OPT") is None
    assert env.optional("MCNB_T_OPT", "d") == "d"


@pytest.mark.parametrize(
    "value,expected",
    [
        ("", "****"),
        (None, "****"),
        ("abc", "***"),
        ("abcd", "****"),
        ("supersecret1234", "****1234"),
    ],
)
def test_mask(value, expected):
    assert env.mask(value) == expected


def test_mask_never_reveals_more_than_show_last():
    assert "supersecret" not in env.mask("supersecret1234")
