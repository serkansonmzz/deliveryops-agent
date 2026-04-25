from pathlib import Path

from app.schemas.delivery_state import DeliveryState
from app.tools.delivery_report_tools import build_progress_comment
from app.tools.github_tools import add_github_issue_comment


def ensure_issue_available(state: DeliveryState) -> None:
    if not state.github_owner or not state.github_repo:
        raise RuntimeError("GitHub owner/repo is missing from state.")

    if not state.github_issue_number:
        raise RuntimeError("GitHub issue number is missing from state.")


def post_progress_comment(repo_path: Path, state: DeliveryState) -> str:
    ensure_issue_available(state)

    comment_body = build_progress_comment(state)

    return add_github_issue_comment(
        owner=state.github_owner,
        repo=state.github_repo,
        issue_number=state.github_issue_number,
        body=comment_body,
    )