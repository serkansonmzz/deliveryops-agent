from pathlib import Path

from app.adapters.command_result import CommandResult
from app.adapters.process_adapter import run_process, run_process_or_raise


def run_git(args: list[str], cwd: Path) -> CommandResult:
    return run_process(["git", *args], cwd=cwd)


def run_git_or_raise(args: list[str], cwd: Path) -> CommandResult:
    return run_process_or_raise(["git", *args], cwd=cwd)


def get_current_git_branch(repo_path: Path) -> str:
    result = run_git_or_raise(
        ["rev-parse", "--abbrev-ref", "HEAD"],
        cwd=repo_path,
    )

    return result.stdout.strip()


def get_git_changed_files(repo_path: Path) -> list[str]:
    result = run_git_or_raise(
        ["status", "--short"],
        cwd=repo_path,
    )

    files: list[str] = []

    for line in result.stdout.splitlines():
        if not line.strip():
            continue

        file_path = line[3:].strip()

        if file_path:
            files.append(file_path)

    return files


def git_working_tree_is_clean(repo_path: Path) -> bool:
    result = run_git_or_raise(
        ["status", "--porcelain"],
        cwd=repo_path,
    )

    return not result.stdout.strip()
