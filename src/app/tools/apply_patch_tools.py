from pathlib import Path
from app.tools.patch_file_tools import (
    has_generated_patch,
    get_default_patch_path,
    apply_unified_diff_patch,
    PatchApplyResult
)
from app.schemas.delivery_state import DeliveryState


def build_patch_note_content(state: DeliveryState) -> str:
    lines: list[str] = []

    lines.append("# DeliveryOps Patch Note")
    lines.append("")
    lines.append("## Request")
    lines.append("")
    lines.append(state.original_request)
    lines.append("")

    lines.append("## GitHub Tracking")
    lines.append("")
    lines.append(f"- Issue: {state.github_issue_url or 'pending'}")
    lines.append(f"- Branch: {state.branch_name or 'pending'}")
    lines.append("")

    lines.append("## Patch Summary")
    lines.append("")
    lines.append(state.patch_summary or "No patch summary available.")
    lines.append("")

    lines.append("## Proposed Changes")
    lines.append("")

    if state.proposed_changes:
        for index, change in enumerate(state.proposed_changes, start=1):
            lines.append(f"{index}. {change}")
    else:
        lines.append("No proposed changes were recorded.")

    lines.append("")

    return "\n".join(lines)


def apply_patch_note(repo_path: Path, state: DeliveryState) -> Path:
    output_path = repo_path / ".deliveryops" / "PATCH_NOTE.md"
    output_path.parent.mkdir(exist_ok=True)

    output_path.write_text(
        build_patch_note_content(state),
        encoding="utf-8",
    )

    return output_path



def apply_available_patch(repo_path: Path, state: DeliveryState) -> PatchApplyResult | Path:
    if has_generated_patch(repo_path):
        patch_path = get_default_patch_path(repo_path)
        return apply_unified_diff_patch(repo_path, patch_path)

    return apply_patch_note(repo_path, state)