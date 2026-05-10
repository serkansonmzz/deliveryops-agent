from pathlib import Path

from app.schemas.delivery_state import DeliveryState
from app.schemas.final_report import FinalReport
from app.tools.commit_tools import filter_commit_files


def _format_plan_step(index: int, step: str) -> str:
    stripped = step.strip()
    prefix = f"{index}. "
    if stripped.startswith(prefix):
        return stripped
    return f"{index}. {stripped}"


def _workflow_summary(state: DeliveryState) -> str:
    outcomes: list[str] = []

    if "apply_patch" in state.completed_steps:
        outcomes.append("patch applied")
    if state.test_status == "passed":
        outcomes.append("tests passed")
    if state.commit_hash:
        outcomes.append("commit created")
    if state.push_status == "pushed":
        outcomes.append("branch pushed")
    if state.pr_url:
        outcomes.append("draft PR opened")

    if outcomes:
        return "DeliveryOps completed: " + ", ".join(outcomes) + "."

    return state.patch_summary or "DeliveryOps workflow completed."


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
    changed_files = filter_commit_files(state.committed_files or state.changed_files)

    lines: list[str] = []

    lines.append("# DeliveryOps Final Report")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(_workflow_summary(state))
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
            lines.append(_format_plan_step(index, step))
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

    lines.append("## Validation")
    lines.append("")
    lines.append(f"- Test Command: `{state.test_command or 'not available'}`")
    lines.append(f"- Test Status: `{state.test_status or 'not available'}`")
    lines.append(
        f"- Test Exit Code: `{state.test_exit_code if state.test_exit_code is not None else 'not available'}`"
    )
    lines.append(f"- CI Status: `{state.ci_status or 'not available'}`")
    lines.append(f"- CI Summary: {state.ci_summary or 'not available'}")
    lines.append(f"- Readiness Status: `{state.readiness_status or 'not available'}`")
    lines.append(f"- Readiness Risk: `{state.readiness_risk_level or 'not available'}`")
    lines.append("")

    if state.dev_context_status in {"patch_generation_failed", "patch_generation_retrying"} or state.last_error:
        lines.append("## Patch Generation Notes")
        lines.append("")
        lines.append(f"- Dev Context Status: `{state.dev_context_status or 'not available'}`")
        lines.append(
            f"- Blocked Reason: `{state.patch_generation_blocked_reason or 'not available'}`"
        )
        lines.append(f"- Last Error: {state.last_error or 'not available'}")
        if state.patch_generation_attempts:
            lines.append("")
            lines.append("### Attempts")
            lines.append("")
            for attempt in state.patch_generation_attempts:
                lines.append(
                    "- "
                    f"Attempt `{attempt.get('attempt')}` "
                    f"mode `{attempt.get('mode')}` "
                    f"status `{attempt.get('status')}` "
                    f"elapsed `{attempt.get('elapsed_seconds')}`s"
                )
                if attempt.get("error"):
                    lines.append(f"  Error: {attempt.get('error')}")
        lines.append("")

    lines.append("## Dev Agent Context")
    lines.append("")
    lines.append("### Selected Files")
    if state.dev_context_selected_files:
        for file_path in state.dev_context_selected_files:
            lines.append(f"- `{file_path}`")
    else:
        lines.append("- not available")
    lines.append("")
    lines.append("### Related Tests")
    if state.dev_context_related_tests:
        for file_path in state.dev_context_related_tests:
            lines.append(f"- `{file_path}`")
    else:
        lines.append("- not available")
    lines.append("")

    lines.append("## Warnings")
    lines.append("")
    warnings = state.readiness_warnings or state.policy_warnings
    if warnings:
        for warning in warnings:
            lines.append(f"- {warning}")
    else:
        lines.append("- none")
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
