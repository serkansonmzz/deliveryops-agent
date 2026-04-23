from pathlib import Path

from app.schemas.delivery_state import DeliveryState


def read_text_file(path: Path, max_chars: int = 8000) -> str:
    content = path.read_text(encoding="utf-8")
    return content[:max_chars]


def collect_repo_context(repo_path: Path, state: DeliveryState, max_files: int = 5) -> dict:
    likely_files = state.likely_files[:max_files]
    collected_files: list[dict] = []

    for relative_path in likely_files:
        file_path = repo_path / relative_path

        if not file_path.exists() or not file_path.is_file():
            continue

        try:
            content = read_text_file(file_path)
        except UnicodeDecodeError:
            continue

        collected_files.append(
            {
                "path": relative_path,
                "content": content,
            }
        )

    return {
        "request": state.original_request,
        "issue_url": state.github_issue_url,
        "branch_name": state.branch_name,
        "architecture_review_summary": state.architecture_review_summary,
        "implementation_plan": state.implementation_plan,
        "likely_files": state.likely_files,
        "files": collected_files,
    }