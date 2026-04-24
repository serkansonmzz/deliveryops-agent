from pathlib import Path
import subprocess

import pytest

from app.tools.push_tools import (
    ensure_push_safe_branch,
    push_current_branch,
)


def init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, check=True)


def test_ensure_push_safe_branch_rejects_main():
    with pytest.raises(RuntimeError):
        ensure_push_safe_branch("main")


def test_ensure_push_safe_branch_rejects_master():
    with pytest.raises(RuntimeError):
        ensure_push_safe_branch("master")


def test_ensure_push_safe_branch_accepts_feature_branch():
    ensure_push_safe_branch("feature/test-branch")


def test_push_current_branch_to_bare_remote(tmp_path: Path):
    repo_path = tmp_path / "repo"
    remote_path = tmp_path / "remote.git"

    repo_path.mkdir()

    subprocess.run(["git", "init", "--bare", str(remote_path)], check=True, stdout=subprocess.PIPE)

    init_git_repo(repo_path)

    readme = repo_path / "README.md"
    readme.write_text("# Test Project\n", encoding="utf-8")

    subprocess.run(["git", "add", "README.md"], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "chore: initial commit"], cwd=repo_path, check=True)
    subprocess.run(["git", "checkout", "-b", "feature/test-push"], cwd=repo_path, check=True)
    subprocess.run(["git", "remote", "add", "origin", str(remote_path)], cwd=repo_path, check=True)

    result = push_current_branch(repo_path)

    assert result.pushed is True
    assert result.remote == "origin"
    assert result.branch_name == "feature/test-push"