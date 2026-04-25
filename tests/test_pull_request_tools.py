from pathlib import Path
import subprocess

import pytest

from app.schemas.delivery_state import DeliveryState
from app.tools import pull_request_tools
from app.tools.github_tools import GitHubCommandResult
from app.tools.pull_request_tools import (
    ensure_pr_safe_branch,
    build_pull_request_title,
    build_pull_request_body,
    create_draft_pull_request,
)


def init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, check=True)


def test_ensure_pr_safe_branch_rejects_main():
    with pytest.raises(RuntimeError):
        ensure_pr_safe_branch("main")


def test_ensure_pr_safe_branch_rejects_master():
    with pytest.raises(RuntimeError):
        ensure_pr_safe_branch("master")


def test_ensure_pr_safe_branch_accepts_feature_branch():
    ensure_pr_safe_branch("feature/test-pr")


def test_build_pull_request_title_uses_commit_message():
    state = DeliveryState(
        request_id="req_test",
        repo_path="/tmp/repo",
        original_request="Add draft PR support",
        commit_message="feat: add draft PR support",
    )

    title = build_pull_request_title(state)

    assert title == "feat: add draft PR support"


def test_build_pull_request_body_contains_tracking_info():
    state = DeliveryState(
        request_id="req_test",
        repo_path="/tmp/repo",
        original_request="Add draft PR support",
        github_issue_url="https://github.com/test/repo/issues/1",
        commit_hash="abc1234",
        committed_files=["src/app/main.py"],
    )

    body = build_pull_request_body(state)

    assert "Add draft PR support" in body
    assert "abc1234" in body
    assert "src/app/main.py" in body


def test_create_draft_pull_request(monkeypatch, tmp_path: Path):
    init_git_repo(tmp_path)

    readme = tmp_path / "README.md"
    readme.write_text("# Test Project\n", encoding="utf-8")

    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "chore: initial commit"], cwd=tmp_path, check=True)
    subprocess.run(["git", "checkout", "-b", "feature/test-pr"], cwd=tmp_path, check=True)

    def fake_run_gh(args, cwd=None):
        if args == ["--version"]:
            return GitHubCommandResult(
                command=["gh", "--version"],
                return_code=0,
                stdout="gh version 2.x",
                stderr="",
            )

        if args == ["auth", "status"]:
            return GitHubCommandResult(
                command=["gh", "auth", "status"],
                return_code=0,
                stdout="Logged in",
                stderr="",
            )

        assert args[0:2] == ["pr", "create"]
        assert "--draft" in args

        return GitHubCommandResult(
            command=["gh", *args],
            return_code=0,
            stdout="https://github.com/test/repo/pull/1",
            stderr="",
        )

    monkeypatch.setattr(pull_request_tools, "run_gh", fake_run_gh)

    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Add draft PR support",
        commit_message="feat: add draft PR support",
        committed_files=["README.md"],
    )

    result = create_draft_pull_request(tmp_path, state)

    assert result.url.endswith("/pull/1")
    assert result.draft is True
    assert result.head_branch == "feature/test-pr"