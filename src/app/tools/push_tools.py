from pathlib import Path

from app.schemas.push_result import PushResult
from app.tools.git_tools import get_current_branch, run_git


PROTECTED_BRANCHES = {"main", "master"}


def ensure_push_safe_branch(branch_name: str) -> None:
    if branch_name in PROTECTED_BRANCHES:
        raise RuntimeError(
            f"Refusing to push protected branch directly: {branch_name}"
        )

    if not branch_name:
        raise RuntimeError("Current branch could not be detected.")


def push_current_branch(
    repo_path: Path,
    remote: str = "origin",
) -> PushResult:
    branch_name = get_current_branch(repo_path)
    ensure_push_safe_branch(branch_name)

    result = run_git(repo_path, ["push", "-u", remote, branch_name])

    if result.return_code != 0:
        raise RuntimeError(result.stderr)

    return PushResult(
        remote=remote,
        branch_name=branch_name,
        pushed=True,
        stdout=result.stdout,
        stderr=result.stderr,
    )