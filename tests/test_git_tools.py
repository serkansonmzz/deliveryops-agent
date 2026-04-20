import subprocess
from pathlib import Path

import pytest

from app.tools.git_tools import ensure_git_repo, get_current_branch, get_git_status


def test_ensure_git_repo_raises_for_non_repo(tmp_path: Path):
    with pytest.raises(ValueError):
        ensure_git_repo(tmp_path)


def test_git_status_in_initialized_repo(tmp_path: Path):
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True)

    branch = get_current_branch(tmp_path)
    status = get_git_status(tmp_path)

    assert branch in {"main", "master", ""}
    assert status == ""