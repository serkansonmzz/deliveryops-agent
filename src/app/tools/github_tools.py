import json
import subprocess
from pathlib import Path

from pydantic import BaseModel


class GitHubCommandResult(BaseModel):
    command: list[str]
    return_code: int
    stdout: str
    stderr: str


class GitHubIssue(BaseModel):
    number: int
    url: str
    title: str


def run_gh(args: list[str], cwd: Path | None = None) -> GitHubCommandResult:
    command = ["gh", *args]

    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    return GitHubCommandResult(
        command=command,
        return_code=result.returncode,
        stdout=result.stdout.strip(),
        stderr=result.stderr.strip(),
    )


def ensure_gh_available() -> None:
    result = run_gh(["--version"])

    if result.return_code != 0:
        raise RuntimeError(
            "GitHub CLI is not available. Install gh first or make sure it is in PATH."
        )


def ensure_gh_authenticated() -> None:
    ensure_gh_available()

    result = run_gh(["auth", "status"])

    if result.return_code != 0:
        raise RuntimeError("GitHub CLI is not authenticated. Run: gh auth login")


def create_github_issue(
    owner: str,
    repo: str,
    title: str,
    body: str,
    labels: list[str] | None = None,
) -> GitHubIssue:
    ensure_gh_authenticated()

    repo_slug = f"{owner}/{repo}"

    args = [
        "issue",
        "create",
        "--repo",
        repo_slug,
        "--title",
        title,
        "--body",
        body,
    ]

    if labels:
        for label in labels:
            args.extend(["--label", label])

    result = run_gh(args)

    if result.return_code != 0:
        raise RuntimeError(result.stderr)

    url = result.stdout.strip()
    number = int(url.rstrip("/").split("/")[-1])

    return GitHubIssue(
        number=number,
        url=url,
        title=title,
    )


def add_github_issue_comment(
    owner: str,
    repo: str,
    issue_number: int,
    body: str,
) -> str:
    ensure_gh_authenticated()

    repo_slug = f"{owner}/{repo}"

    result = run_gh(
        [
            "issue",
            "comment",
            str(issue_number),
            "--repo",
            repo_slug,
            "--body",
            body,
        ]
    )

    if result.return_code != 0:
        raise RuntimeError(result.stderr)

    return result.stdout