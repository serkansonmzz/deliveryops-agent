from pathlib import Path

from app.schemas.delivery_state import DeliveryState
from app.tools.dev_context_tools import (
    apply_dev_context_tracking_to_state,
    build_dev_patch_context,
)


def collect_repo_context(repo_path: Path, state: DeliveryState, max_files: int = 5) -> dict:
    dev_patch_context = build_dev_patch_context(repo_path, state)
    apply_dev_context_tracking_to_state(state, dev_patch_context)

    collected_files = [
        {
            "path": file.path,
            "content": file.content,
        }
        for file in dev_patch_context.selected_files[:max_files]
    ]
    likely_files = dev_patch_context.allowed_target_files or state.likely_files

    return {
        "request": state.original_request,
        "issue_url": state.github_issue_url,
        "branch_name": state.branch_name,
        "architecture_review_summary": state.architecture_review_summary,
        "implementation_plan": state.implementation_plan,
        "likely_files": likely_files,
        "files": collected_files,
        "dev_patch_context": dev_patch_context.as_prompt_text(),
    }
