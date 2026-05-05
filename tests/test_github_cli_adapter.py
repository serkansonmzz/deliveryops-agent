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
