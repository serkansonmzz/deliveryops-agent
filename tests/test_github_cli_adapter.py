import pytest

from app.adapters import github_cli_adapter
from app.adapters.command_result import CommandResult


def test_get_pr_checks_uses_gh_pr_checks(monkeypatch, tmp_path):
    captured = {}

    def fake_run_process(args, cwd, timeout_seconds=None):
        captured["args"] = args
        captured["cwd"] = cwd
        return CommandResult(
            args=args,
            return_code=0,
            stdout="build pass\n",
            stderr="",
        )

    monkeypatch.setattr(github_cli_adapter, "run_process", fake_run_process)

    result = github_cli_adapter.get_pr_checks("feature/test", tmp_path)

    assert result.ok is True
    assert captured["args"] == ["gh", "pr", "checks", "feature/test"]
    assert captured["cwd"] == tmp_path


def test_ensure_gh_authenticated_raises_when_auth_fails(monkeypatch, tmp_path):
    def fake_run_gh(args, cwd):
        return CommandResult(
            args=["gh", *args],
            return_code=1,
            stdout="",
            stderr="not logged in",
        )

    monkeypatch.setattr(github_cli_adapter, "check_gh_installed", lambda cwd: None)
    monkeypatch.setattr(github_cli_adapter, "run_gh", fake_run_gh)

    with pytest.raises(RuntimeError) as exc:
        github_cli_adapter.ensure_gh_authenticated(tmp_path)

    assert "gh auth login" in str(exc.value)


def test_get_pr_checks_json_uses_json_flags(monkeypatch, tmp_path):
    captured = {}

    def fake_run_gh(args, cwd):
        captured["args"] = args
        captured["cwd"] = cwd
        return CommandResult(
            args=["gh", *args],
            return_code=0,
            stdout="[]",
            stderr="",
        )

    monkeypatch.setattr(github_cli_adapter, "run_gh", fake_run_gh)

    result = github_cli_adapter.get_pr_checks_json("feature/test", tmp_path)

    assert result.ok is True
    assert captured["args"] == [
        "pr",
        "checks",
        "feature/test",
        "--json",
        "name,state,conclusion,link",
    ]
    assert captured["cwd"] == tmp_path
