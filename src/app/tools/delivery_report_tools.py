from pathlib import Path

from app.schemas.delivery_state import DeliveryState
from app.schemas.final_report import FinalReport


def build_progress_comment(state: DeliveryState) -> str:
    lines: list[str] = []

    lines.append("## DeliveryOps Progress Update")
    lines.append("")
    lines.append(f"- Request ID: `{state.request_id}`")
    lines.append(f"- Current Step: `{state.current_step}`")
    lines.append(f"- Branch: `{state.branch_name or 'not available'}`")
    lines.append(f"- Commit: `{state.commit_hash or 'not available'}`")
    lines.append(f"- Pull Request: {state.pr_url or 'not available'}")
    lines.append("")

    lines.append("### Completed Steps")
    lines.append("")

    if state.completed_steps:
        for step in state.completed_steps:
            lines.append(f"- [x] {step}")
    else:
        lines.append("- none")

    lines.append("")

    lines.append("### Changed Files")
    lines.append("")

    files = state.committed_files or state.changed_files

    if files:
        for file_path in files:
            lines.append(f"- `{file_path}`")
    else:
        lines.append("- not available")

    lines.append("")

    if state.pending_approval and state.pending_action:
        lines.append("### Pending Approval")
        lines.append("")
        lines.append(f"- `{state.pending_action}`")
        lines.append("")

    return "\n".join(lines)


def build_final_report(state: DeliveryState) -> FinalReport:
    changed_files = state.committed_files or state.changed_files

    lines: list[str] = []

    lines.append("# DeliveryOps Final Report")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(state.patch_summary or "DeliveryOps workflow completed.")
    lines.append("")

    lines.append("## Request")
    lines.append("")
    lines.append(state.original_request)
    lines.append("")

    lines.append("## Tracking")
    lines.append("")
    lines.append(f"- Request ID: `{state.request_id}`")
    lines.append(f"- GitHub Issue: {state.github_issue_url or 'not available'}")
    lines.append(f"- Branch: `{state.branch_name or 'not available'}`")
    lines.append(f"- Commit: `{state.commit_hash or 'not available'}`")
    lines.append(f"- Pull Request: {state.pr_url or 'not available'}")
    lines.append("")

    lines.append("## Architecture Review")
    lines.append("")
    lines.append(state.architecture_review_summary or "not available")
    lines.append("")

    lines.append("## Implementation Plan")
    lines.append("")

    if state.implementation_plan:
        for index, step in enumerate(state.implementation_plan, start=1):
            lines.append(f"{index}. {step}")
    else:
        lines.append("not available")

    lines.append("")

    lines.append("## Changed Files")
    lines.append("")

    if changed_files:
        for file_path in changed_files:
            lines.append(f"- `{file_path}`")
    else:
        lines.append("- not available")

    lines.append("")

    lines.append("## Commit")
    lines.append("")
    lines.append(f"- Message: `{state.commit_message or 'not available'}`")
    lines.append(f"- Hash: `{state.commit_hash or 'not available'}`")
    lines.append("")

    lines.append("## Pull Request")
    lines.append("")
    lines.append(f"- Title: `{state.pr_title or 'not available'}`")
    lines.append(f"- URL: {state.pr_url or 'not available'}")
    lines.append(f"- Status: `{state.pr_status or 'not available'}`")
    lines.append("")

    lines.append("## Completed Steps")
    lines.append("")

    if state.completed_steps:
        for step in state.completed_steps:
            lines.append(f"- [x] {step}")
    else:
        lines.append("- none")

    lines.append("")

    return FinalReport(
        title="DeliveryOps Final Report",
        body="\n".join(lines),
        changed_files=changed_files,
        issue_url=state.github_issue_url,
        pr_url=state.pr_url,
        commit_hash=state.commit_hash,
    )


def write_final_report(repo_path: Path, report: FinalReport) -> Path:
    workspace = repo_path / ".deliveryops"
    workspace.mkdir(exist_ok=True)

    report_path = workspace / "FINAL_REPORT.md"
    report_path.write_text(report.body, encoding="utf-8")

    return report_path