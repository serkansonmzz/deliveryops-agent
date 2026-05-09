from pathlib import Path

from app.schemas.commit_message import CommitMessageSpec
from app.schemas.delivery_state import DeliveryState
from app.tools.commit_tools import filter_commit_files
from app.tools.git_tools import run_git
from app.tools.patch_file_tools import get_changed_files


def normalize_request_text(request: str, max_length: int = 58) -> str:
    cleaned = " ".join(request.strip().split())

    if not cleaned:
        return "update deliveryops workflow"

    cleaned = cleaned[0].lower() + cleaned[1:]

    if len(cleaned) <= max_length:
        return cleaned

    truncated = cleaned[:max_length].rstrip(" .,;:-")
    if " " in truncated:
        truncated = truncated.rsplit(" ", 1)[0]
    return truncated.rstrip(" .,;:-")


def infer_commit_type(request: str, changed_files: list[str]) -> str:
    request_lower = request.lower()
    files_text = " ".join(changed_files).lower()

    if "fix" in request_lower or "bug" in request_lower or "error" in request_lower:
        return "fix"

    if "refactor" in request_lower:
        return "refactor"

    has_source = any(
        file.endswith((".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".cs"))
        and not file.startswith("tests/")
        and "/tests/" not in file
        and "test_" not in Path(file).name
        for file in changed_files
    )
    has_tests = "tests/" in files_text or "test_" in files_text
    has_docs = any(
        file.lower().endswith((".md", ".rst", ".txt")) or Path(file).name.lower() == "readme.md"
        for file in changed_files
    )

    if has_source:
        return "feat"

    if has_tests:
        return "test"

    if has_docs or "readme" in request_lower or "docs" in request_lower or "documentation" in request_lower:
        return "docs"

    if "pyproject.toml" in files_text or ".gitignore" in files_text:
        return "chore"

    return "feat"


def build_subject_text(request: str, changed_files: list[str]) -> str:
    request_lower = request.lower()
    files_text = " ".join(changed_files).lower()

    if "calculator" in request_lower and (
        "cli" in request_lower or "command-line interface" in request_lower
    ):
        return "add calculator CLI"

    if "subtract" in request_lower and "calculator" in request_lower:
        return "add calculator subtraction support"

    if "multiply" in request_lower and "calculator" in request_lower:
        return "add calculator multiplication support"

    if "command-line interface" in request_lower:
        return "add command-line interface"

    if "add" in request_lower and "function" in request_lower:
        for file_path in changed_files:
            if file_path.endswith(".py") and not file_path.startswith("tests/"):
                return normalize_request_text(request.replace("function to", "support in"))

    return normalize_request_text(request)


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


def get_filtered_git_diff(repo_path: Path, changed_files: list[str], staged: bool) -> str:
    if not changed_files:
        return ""

    args = ["diff", "--staged"] if staged else ["diff"]
    args.extend(["--", *changed_files])
    result = run_git(repo_path, args)

    if result.return_code != 0:
        raise RuntimeError(result.stderr)

    return result.stdout


def build_commit_message_spec(repo_path: Path, state: DeliveryState) -> CommitMessageSpec:
    changed_files = filter_commit_files(get_changed_files(repo_path))

    unstaged_diff = get_filtered_git_diff(repo_path, changed_files, staged=False)
    staged_diff = get_filtered_git_diff(repo_path, changed_files, staged=True)

    diff_text = "\n".join(part for part in [staged_diff, unstaged_diff] if part.strip())

    commit_type = infer_commit_type(state.original_request, changed_files)
    subject_text = build_subject_text(state.original_request, changed_files)

    subject = f"{commit_type}: {subject_text}"

    if len(subject) > 72:
        truncated = subject[:72].rstrip(" .,;:-")
        if " " in truncated:
            truncated = truncated.rsplit(" ", 1)[0]
        subject = truncated.rstrip(" .,;:-")

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
