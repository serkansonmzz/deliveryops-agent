from pathlib import Path
from app.schemas.delivery_state import DeliveryState


CHECKLIST_STEPS = [
    ("inspect_repository", "Inspect repository"),
    ("initialize_workspace", "Initialize local DeliveryOps workspace"),
    ("analyze_feature_request", "Analyze feature request"),
    ("create_github_issue", "Create GitHub issue"),
    ("create_feature_branch", "Create feature branch"),
    ("run_architecture_review", "Run architecture mini-review"),
    ("generate_implementation_plan", "Generate implementation plan"),
    ("prepare_patch", "Prepare patch"),
    ("request_patch_approval", "Request approval to apply patch"),
    ("apply_patch", "Apply patch"),
    ("detect_test_command", "Detect test command"),
    ("run_tests", "Run tests"),
    ("generate_commit_message", "Generate commit message"),
    ("request_commit_approval", "Request approval for commit"),
    ("commit_changes", "Commit changes"),
    ("request_push_approval", "Request approval for push"),
    ("push_branch", "Push branch"),
    ("request_pr_approval", "Request approval for draft PR"),
    ("open_draft_pr", "Open draft PR"),
    ("update_github_issue", "Update GitHub issue"),
    ("produce_final_report", "Produce final delivery report"),
]


def render_delivery_markdown(state: DeliveryState) -> str:
    lines: list[str] = []

    lines.append("# DeliveryOps Runbook")
    lines.append("")
    lines.append("## Request")
    lines.append("")
    lines.append(state.original_request)
    lines.append("")

    lines.append("## Tracking")
    lines.append("")
    lines.append(f"- Request ID: `{state.request_id}`")
    lines.append(f"- GitHub Issue: `{state.github_issue_url or 'pending'}`")
    lines.append(f"- Branch: `{state.branch_name or 'pending'}`")
    lines.append(f"- Draft PR: `{state.pr_url or 'pending'}`")
    lines.append(f"- Current Step: `{state.current_step}`")
    lines.append(f"- Pending Approval: `{state.pending_approval}`")
    lines.append("")

    lines.append("## Checklist")
    lines.append("")

    for step_key, label in CHECKLIST_STEPS:
        checked = "x" if step_key in state.completed_steps else " "
        lines.append(f"- [{checked}] {label}")
        lines.append("## Architecture Review Summary")
    lines.append("")
    lines.append(state.architecture_review_summary or "pending")
    lines.append("")

    lines.append("### Detected Stack")
    lines.append("")
    if state.detected_stack:
        for item in state.detected_stack:
            lines.append(f"- `{item}`")
    else:
        lines.append("- pending")
    lines.append("")

    lines.append("### Affected Areas")
    lines.append("")
    if state.affected_areas:
        for item in state.affected_areas:
            lines.append(f"- {item}")
    else:
        lines.append("- pending")
    lines.append("")

    lines.append("### Likely Files")
    lines.append("")
    if state.likely_files:
        for item in state.likely_files:
            lines.append(f"- `{item}`")
    else:
        lines.append("- pending")
    lines.append("")

    lines.append("### Risk Notes")
    lines.append("")
    if state.risk_notes:
        for item in state.risk_notes:
            lines.append(f"- {item}")
    else:
        lines.append("- pending")
    lines.append("")

    lines.append("## Implementation Plan")
    lines.append("")
    if state.implementation_plan:
        for index, step in enumerate(state.implementation_plan, start=1):
            lines.append(f"{index}. {step}")
    else:
        lines.append("pending")
    lines.append("")
    lines.append("## Patch Summary")
    lines.append("")
    lines.append(state.patch_summary or "pending")
    lines.append("")

    lines.append("### Patch Affected Files")
    lines.append("")
    if state.patch_affected_files:
        for item in state.patch_affected_files:
            lines.append(f"- `{item}`")
    else:
        lines.append("- pending")
    lines.append("")

    lines.append("### Proposed Changes")
    lines.append("")
    if state.proposed_changes:
        for index, item in enumerate(state.proposed_changes, start=1):
            lines.append(f"{index}. {item}")
    else:
        lines.append("pending")
    lines.append("")

    lines.append("## Commit Message Proposal")
    lines.append("")
    lines.append(f"- Subject: `{state.commit_message or 'pending'}`")
    lines.append(f"- Commit Hash: `{state.commit_hash or 'pending'}`")
    lines.append("")

    lines.append("## Push Status")
    lines.append("")
    lines.append(f"- Remote: `{state.push_remote or 'pending'}`")
    lines.append(f"- Branch: `{state.pushed_branch or 'pending'}`")
    lines.append(f"- Status: `{state.push_status or 'pending'}`")
    lines.append(f"- Output: `{state.push_output or 'pending'}`")
    lines.append("")

    lines.append("## Pull Request Status")
    lines.append("")
    lines.append(f"- URL: `{state.pr_url or 'pending'}`")
    lines.append(f"- Title: `{state.pr_title or 'pending'}`")
    lines.append(f"- Base Branch: `{state.pr_base_branch or 'pending'}`")
    lines.append(f"- Head Branch: `{state.pr_head_branch or 'pending'}`")
    lines.append(f"- Status: `{state.pr_status or 'pending'}`")
    lines.append("")
    lines.append("### Pull Request Body")
    lines.append("")
    lines.append(state.pr_body or "pending")
    lines.append("")

    lines.append("## Issue Comment Status")
    lines.append("")
    lines.append(f"- Comment Count: `{state.issue_comment_count}`")
    lines.append(f"- Last Comment URL: `{state.last_issue_comment_url or 'pending'}`")
    lines.append("")

    lines.append("## Final Report")
    lines.append("")
    lines.append(f"- Path: `{state.final_report_path or 'pending'}`")
    lines.append(f"- Status: `{state.final_report_status or 'pending'}`")
    lines.append("")

    lines.append("### Committed Files")
    lines.append("")
    if state.committed_files:
        for file_path in state.committed_files:
            lines.append(f"- `{file_path}`")
    else:
        lines.append("- pending")
    lines.append("")
    lines.append("### Commit Body")
    lines.append("")
    lines.append(state.commit_body or "pending")
    lines.append("")
    lines.append("### Commit Diff Summary")
    lines.append("")
    lines.append(state.commit_diff_summary or "pending")
    lines.append("")
    lines.append("### Commit Rationale")
    lines.append("")
    lines.append(state.commit_rationale or "pending")
    lines.append("")

    lines.append("### Patch Risk Level")
    lines.append("")
    lines.append(state.patch_risk_level or "pending")
    lines.append("")

    lines.append("## Test Results")
    lines.append("")
    lines.append(f"- Command: `{state.test_command or 'pending'}`")
    lines.append(f"- Status: `{state.test_status or 'pending'}`")
    lines.append(
        f"- Exit Code: `{state.test_exit_code if state.test_exit_code is not None else 'pending'}`"
    )
    lines.append("")
    lines.append("### Test Summary")
    lines.append("")
    lines.append(state.test_summary or "pending")
    lines.append("")

    lines.append("## Test Failure Analysis")
    lines.append("")
    lines.append(f"- Category: `{state.test_failure_category or 'pending'}`")
    lines.append(f"- Risk Level: `{state.test_failure_risk_level or 'pending'}`")
    lines.append("")
    lines.append("### Failure Summary")
    lines.append("")
    lines.append(state.test_failure_analysis_summary or "pending")
    lines.append("")
    lines.append("### Likely Causes")
    lines.append("")
    if state.test_failure_likely_causes:
        for cause in state.test_failure_likely_causes:
            lines.append(f"- {cause}")
    else:
        lines.append("- pending")
    lines.append("")
    lines.append("### Recommended Next Actions")
    lines.append("")
    if state.test_failure_next_actions:
        for action in state.test_failure_next_actions:
            lines.append(f"- {action}")
    else:
        lines.append("- pending")
    lines.append("")

    lines.append("## Changed Files")
    lines.append("")

    if state.changed_files:
        for file_path in state.changed_files:
            lines.append(f"- `{file_path}`")
    else:
        lines.append("- pending")

    lines.append("")
    lines.append("## Last Agent Notes")
    lines.append("")
    lines.append(state.last_error or "No notes yet.")
    lines.append("")

    lines.append("## Next Action")
    lines.append("")
    if state.pending_approval and state.pending_action:
        lines.append(f"Waiting for approval: `{state.pending_action}`")
    else:
        lines.append(f"Continue from step: `{state.current_step}`")

    lines.append("")

    return "\n".join(lines)


def update_delivery_markdown(state: DeliveryState) -> Path:
    workspace = Path(state.repo_path) / ".deliveryops"
    workspace.mkdir(exist_ok=True)

    output_path = workspace / "DELIVERY.md"
    output_path.write_text(render_delivery_markdown(state), encoding="utf-8")

    return output_path