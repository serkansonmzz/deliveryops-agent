from pathlib import Path

from app.adapters.command_result import CommandResult
from app.adapters.process_adapter import run_process


def run_gh(args: list[str], cwd: Path) -> CommandResult:
    return run_process(["gh", *args], cwd=cwd)


def ensure_gh_authenticated(cwd: Path) -> None:
    result = run_gh(["auth", "status"], cwd=cwd)

    if not result.ok:
        raise RuntimeError(
            "GitHub CLI authentication failed.\n"
            "Run `gh auth login` and try again.\n\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )


def get_pr_checks(branch: str, cwd: Path) -> CommandResult:
    return run_gh(["pr", "checks", branch], cwd=cwd)


def create_issue(
    owner: str,
    repo: str,
    title: str,
    body: str,
    cwd: Path,
) -> CommandResult:
    return run_gh(
        [
            "issue",
            "create",
            "--repo",
            f"{owner}/{repo}",
            "--title",
            title,
            "--body",
            body,
        ],
        cwd=cwd,
    )
