from pathlib import Path

from app.schemas.commit_message import CommitMessageSpec
from app.schemas.delivery_state import DeliveryState
from app.tools.git_tools import get_git_diff
from app.tools.patch_file_tools import get_changed_files


def normalize_request_text(request: str, max_length: int = 58) -> str:
    cleaned = " ".join(request.strip().split())

    if not cleaned:
        return "update deliveryops workflow"

    cleaned = cleaned[0].lower() + cleaned[1:]

    if len(cleaned) <= max_length:
        return cleaned

    return cleaned[:max_length].rstrip(" .,;:-")


def infer_commit_type(request: str, changed_files: list[str]) -> str:
    request_lower = request.lower()
    files_text = " ".join(changed_files).lower()

    if "readme" in request_lower or "docs" in request_lower or "documentation" in request_lower:
        return "docs"

    if "test" in request_lower or "tests/" in files_text or "test_" in files_text:
        return "test"

    if "fix" in request_lower or "bug" in request_lower or "error" in request_lower:
        return "fix"

    if "refactor" in request_lower:
        return "refactor"

    if "pyproject.toml" in files_text or ".gitignore" in files_text:
        return "chore"

    return "feat"


def summarize_diff(diff_text: str, changed_files: list[str]) -> str:
    if not diff_text.strip():
        return "No diff content detected."

    added = 0
    removed = 0

    for line in diff_text.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            added += 1
        elif line.startswith("-") and not line.startswith("---"):
            removed += 1

    files_summary = ", ".join(changed_files) if changed_files else "unknown files"

    return f"Changed files: {files_summary}. Added lines: {added}. Removed lines: {removed}."


def build_commit_message_spec(repo_path: Path, state: DeliveryState) -> CommitMessageSpec:
    changed_files = get_changed_files(repo_path)

    unstaged_diff = get_git_diff(repo_path, staged=False)
    staged_diff = get_git_diff(repo_path, staged=True)

    diff_text = "\n".join(part for part in [staged_diff, unstaged_diff] if part.strip())

    commit_type = infer_commit_type(state.original_request, changed_files)
    subject_text = normalize_request_text(state.original_request)

    subject = f"{commit_type}: {subject_text}"

    if len(subject) > 72:
        subject = subject[:72].rstrip(" .,;:-")

    diff_summary = summarize_diff(diff_text, changed_files)

    body = (
        f"Request ID: {state.request_id}\n"
        f"Issue: {state.github_issue_url or 'not available'}\n\n"
        f"{diff_summary}"
    )

    rationale = (
        "Commit message was generated from the delivery request, changed files, "
        "and current git diff."
    )

    return CommitMessageSpec(
        subject=subject,
        body=body,
        changed_files=changed_files,
        diff_summary=diff_summary,
        rationale=rationale,
    )