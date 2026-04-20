import subprocess
from pathlib import Path
from pydantic import BaseModel


class GitCommandResult(BaseModel):
    command: list[str]
    return_code: int
    stdout: str
    stderr: str


def run_git(repo_path: Path, args: list[str]) -> GitCommandResult:
    command = ["git", *args]

    result = subprocess.run(
        command,
        cwd=repo_path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    return GitCommandResult(
        command=command,
        return_code=result.returncode,
        stdout=result.stdout.strip(),
        stderr=result.stderr.strip(),
    )


def ensure_git_repo(repo_path: Path) -> None:
    result = run_git(repo_path, ["rev-parse", "--is-inside-work-tree"])

    if result.return_code != 0 or result.stdout != "true":
        raise ValueError(f"Not a Git repository: {repo_path}")


def get_current_branch(repo_path: Path) -> str:
    ensure_git_repo(repo_path)

    result = run_git(repo_path, ["branch", "--show-current"])

    if result.return_code != 0:
        raise RuntimeError(result.stderr)

    return result.stdout


def get_git_status(repo_path: Path) -> str:
    ensure_git_repo(repo_path)

    result = run_git(repo_path, ["status", "--short"])

    if result.return_code != 0:
        raise RuntimeError(result.stderr)

    return result.stdout


def get_git_diff(repo_path: Path, staged: bool = False) -> str:
    ensure_git_repo(repo_path)

    args = ["diff", "--staged"] if staged else ["diff"]
    result = run_git(repo_path, args)

    if result.return_code != 0:
        raise RuntimeError(result.stderr)

    return result.stdout


def create_branch(repo_path: Path, branch_name: str) -> str:
    ensure_git_repo(repo_path)

    if branch_name in {"main", "master"}:
        raise ValueError("Refusing to create or switch directly to main/master.")

    result = run_git(repo_path, ["checkout", "-b", branch_name])

    if result.return_code != 0:
        raise RuntimeError(result.stderr)

    return branch_name