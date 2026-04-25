from pathlib import Path

from app.schemas.delivery_state import DeliveryState
from app.schemas.pull_request_result import PullRequestResult
from app.tools.git_tools import get_current_branch
from app.tools.github_tools import ensure_gh_authenticated, run_gh


PROTECTED_BRANCHES = {"main", "master"}


def ensure_pr_safe_branch(branch_name: str) -> None:
    if not branch_name:
        raise RuntimeError("Current branch could not be detected.")

    if branch_name in PROTECTED_BRANCHES:
        raise RuntimeError(
            f"Refusing to open a pull request from protected branch: {branch_name}"
        )


def build_pull_request_title(state: DeliveryState) -> str:
    if state.commit_message:
        return state.commit_message

    if state.github_issue_number:
        return f"DeliveryOps change for issue #{state.github_issue_number}"

    return "DeliveryOps change"


def build_pull_request_body(state: DeliveryState) -> str:
    lines: list[str] = []

    lines.append("## Summary")
    lines.append("")
    lines.append(state.patch_summary or "DeliveryOps generated this change.")
    lines.append("")

    lines.append("## Request")
    lines.append("")
    lines.append(state.original_request)
    lines.append("")

    lines.append("## Tracking")
    lines.append("")
    lines.append(f"- Request ID: `{state.request_id}`")
    lines.append(f"- Issue: {state.github_issue_url or 'not available'}")
    lines.append(f"- Commit: `{state.commit_hash or 'not available'}`")
    lines.append("")

    lines.append("## Changed Files")
    lines.append("")

    files = state.committed_files or state.changed_files

    if files:
        for file_path in files:
            lines.append(f"- `{file_path}`")
    else:
        lines.append("- not available")

    lines.append("")
    lines.append("## Validation")
    lines.append("")
    lines.append("- [ ] Tests reviewed")
    lines.append("- [ ] Patch reviewed")
    lines.append("- [ ] Ready for final review")
    lines.append("")

    return "\n".join(lines)


def create_draft_pull_request(
    repo_path: Path,
    state: DeliveryState,
    base_branch: str = "main",
) -> PullRequestResult:
    ensure_gh_authenticated()

    head_branch = get_current_branch(repo_path)
    ensure_pr_safe_branch(head_branch)

    title = build_pull_request_title(state)
    body = build_pull_request_body(state)

    args = [
        "pr",
        "create",
        "--base",
        base_branch,
        "--head",
        head_branch,
        "--title",
        title,
        "--body",
        body,
        "--draft",
    ]

    result = run_gh(args, cwd=repo_path)

    if result.return_code != 0:
        raise RuntimeError(result.stderr)

    url = result.stdout.strip()

    return PullRequestResult(
        url=url,
        title=title,
        base_branch=base_branch,
        head_branch=head_branch,
        draft=True,
    )