import json
import subprocess
from pathlib import Path

from pydantic import BaseModel, Field


class GitHubCommandResult(BaseModel):
    command: list[str]
    return_code: int
    stdout: str
    stderr: str


class GitHubIssue(BaseModel):
    number: int
    url: str
    title: str
    labels: list[str] = Field(default_factory=list)
    skipped_labels: list[str] = Field(default_factory=list)


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


def list_github_labels(owner: str, repo: str) -> list[str]:
    ensure_gh_authenticated()

    result = run_gh(
        [
            "label",
            "list",
            "--repo",
            f"{owner}/{repo}",
            "--limit",
            "200",
            "--json",
            "name",
        ]
    )

    if result.return_code != 0:
        return []

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []

    if not isinstance(payload, list):
        return []

    labels: list[str] = []
    for item in payload:
        if isinstance(item, dict) and item.get("name"):
            labels.append(str(item["name"]))

    return labels


def filter_existing_labels(
    owner: str,
    repo: str,
    labels: list[str] | None,
) -> tuple[list[str], list[str]]:
    requested = [label.strip() for label in labels or [] if label.strip()]

    if not requested:
        return [], []

    existing = set(list_github_labels(owner, repo))

    if not existing:
        return [], requested

    allowed = [label for label in requested if label in existing]
    skipped = [label for label in requested if label not in existing]
    return allowed, skipped


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

    existing_labels, skipped_labels = filter_existing_labels(owner, repo, labels)

    if existing_labels:
        for label in existing_labels:
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
        labels=existing_labels,
        skipped_labels=skipped_labels,
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
