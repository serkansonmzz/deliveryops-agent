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
    ("detect_tests", "Detect test command"),
    ("run_tests", "Run tests"),
    ("generate_commit_message", "Generate commit message"),
    ("request_commit_approval", "Request approval for commit"),
    ("commit_changes", "Commit changes"),
    ("request_push_approval", "Request approval for push"),
    ("push_branch", "Push branch"),
    ("request_pr_approval", "Request approval for draft PR"),
    ("open_draft_pr", "Open draft PR"),
    ("comment_progress", "Post progress comment"),
    ("generate_final_report", "Produce final delivery report"),
]


def render_delivery_markdown(state: DeliveryState) -> str:
    lines: list[str] = []

    lines.append("# DeliveryOps Runbook")
    lines.append("")
    lines.append("## Request")
    lines.append("")
    lines.append(state.original_request)
    lines.append("")

    lines.append("## Structured Request")
    lines.append("")
    lines.append(f"- Feature Title: `{state.feature_request_title or 'pending'}`")
    lines.append(f"- Issue Spec Title: `{state.issue_spec_title or 'pending'}`")
    lines.append("")
    lines.append("### Feature Summary")
    lines.append("")
    lines.append(state.feature_request_summary or "pending")
    lines.append("")

    lines.append("## Tracking")
    lines.append("")
    lines.append(f"- Request ID: `{state.request_id}`")
    lines.append(f"- GitHub Issue: `{state.github_issue_url or 'pending'}`")
    lines.append(f"- Branch: `{state.branch_name or 'pending'}`")
    lines.append(f"- Draft PR: `{state.pr_url or 'pending'}`")
    lines.append(f"- Current Step: `{state.current_step}`")
    lines.append(f"- Pending Approval: `{state.pending_approval}`")
    lines.append(f"- Policy Profile: `{state.policy_profile}`")
    lines.append("")

    lines.append("## Policy Profile")
    lines.append("")
    lines.append(f"- Active Profile: `{state.policy_profile}`")
    lines.append(f"- Last Policy Decision: `{state.last_policy_decision or 'pending'}`")
    lines.append("")
    lines.append("### Policy Warnings")
    lines.append("")
    if state.policy_warnings:
        for warning in state.policy_warnings:
            lines.append(f"- {warning}")
    else:
        lines.append("- pending")
    lines.append("")

    lines.append("## Agent Role Status")
    lines.append("")
    lines.append(f"- Last Reviewed Role: `{state.last_agent_role_reviewed or 'pending'}`")
    lines.append("")
    lines.append("### Summary")
    lines.append("")
    lines.append(state.agent_role_status_summary or "pending")
    lines.append("")
    lines.append("### Agent Role Notes")
    lines.append("")
    if state.agent_role_notes:
        for note in state.agent_role_notes:
            lines.append(f"- {note}")
    else:
        lines.append("- pending")
    lines.append("")

    approval_heading = (
        "## Pending Approval Request"
        if state.pending_approval and state.pending_action
        else "## Last Approval Request"
    )
    lines.append(approval_heading)
    lines.append("")
    action_text = (
        state.pending_action
        if state.pending_approval and state.pending_action
        else state.approval_request_action or "none"
    )
    lines.append(f"- Action: `{action_text}`")
    lines.append(f"- Risk Level: `{state.approval_request_risk_level or 'pending'}`")
    lines.append("")
    lines.append("### Reason")
    lines.append("")
    lines.append(state.approval_request_reason or "pending")
    lines.append("")
    lines.append("### Affected Files")
    lines.append("")
    if state.approval_request_affected_files:
        for file_path in state.approval_request_affected_files:
            lines.append(f"- `{file_path}`")
    else:
        lines.append("- pending")
    lines.append("")
    lines.append("### Command")
    lines.append("")
    lines.append(f"`{state.approval_request_command or 'pending'}`")
    lines.append("")
    lines.append("### Expected Result")
    lines.append("")
    lines.append(state.approval_request_expected_result or "pending")
    lines.append("")
    lines.append("### Rollback Note")
    lines.append("")
    lines.append(state.approval_request_rollback_note or "pending")
    lines.append("")

    lines.append("## Checklist")
    lines.append("")

    for step_key, label in CHECKLIST_STEPS:
        checked = "x" if step_key in state.completed_steps else " "
        lines.append(f"- [{checked}] {label}")
    lines.append("")

    lines.append("## Architecture Review Summary")
    lines.append("")
    lines.append(state.architecture_review_summary or "pending")
    lines.append("")
    lines.append(f"- Source: `{state.architecture_review_source or 'pending'}`")
    confidence_score = (
        state.architecture_confidence_score
        if state.architecture_confidence_score is not None
        else "pending"
    )
    lines.append(f"- Confidence Score: `{confidence_score}`")
    lines.append("")
    lines.append("### Recommended Approach")
    lines.append("")
    if state.architecture_recommended_approach:
        for item in state.architecture_recommended_approach:
            lines.append(f"- {item}")
    else:
        lines.append("- pending")
    lines.append("")
    lines.append("### Architecture Open Questions")
    lines.append("")
    if state.architecture_open_questions:
        for item in state.architecture_open_questions:
            lines.append(f"- {item}")
    else:
        lines.append("- pending")
    lines.append("")

    lines.append("## Repository Analysis")
    lines.append("")
    lines.append(state.repo_analysis_summary or "pending")
    lines.append("")
    lines.append(f"- Source Files: `{state.repo_source_file_count}`")
    lines.append(f"- Test Files: `{state.repo_test_file_count}`")
    lines.append(f"- Documentation Files: `{state.repo_documentation_file_count}`")
    lines.append(f"- Config Files: `{state.repo_config_file_count}`")
    lines.append("")
    lines.append("### Risky Files")
    lines.append("")
    if state.repo_risky_files:
        for file_path in state.repo_risky_files[:20]:
            lines.append(f"- `{file_path}`")
    else:
        lines.append("- pending")
    lines.append("")
    lines.append("### Source/Test Map")
    lines.append("")
    if state.repo_source_test_map:
        for source_file, test_files in list(state.repo_source_test_map.items())[:20]:
            lines.append(f"- `{source_file}`")
            for test_file in test_files:
                lines.append(f"  - `{test_file}`")
    else:
        lines.append("- pending")
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
            lines.append(f"- `{item}`")
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

    lines.append("### Security Notes")
    lines.append("")
    if state.security_notes:
        for item in state.security_notes:
            lines.append(f"- {item}")
    else:
        lines.append("- pending")
    lines.append("")

    lines.append("### Testing Notes")
    lines.append("")
    if state.testing_notes:
        for item in state.testing_notes:
            lines.append(f"- {item}")
    else:
        lines.append("- pending")
    lines.append("")

    lines.append("### DevOps Notes")
    lines.append("")
    if state.devops_notes:
        for item in state.devops_notes:
            lines.append(f"- {item}")
    else:
        lines.append("- pending")
    lines.append("")

    lines.append("## Implementation Plan")
    lines.append("")
    lines.append(state.implementation_plan_summary or "pending")
    lines.append("")
    lines.append(f"- Source: `{state.implementation_plan_source or 'pending'}`")
    plan_confidence_score = (
        state.implementation_plan_confidence_score
        if state.implementation_plan_confidence_score is not None
        else "pending"
    )
    lines.append(f"- Confidence Score: `{plan_confidence_score}`")
    lines.append("")
    lines.append("### Target Files")
    lines.append("")
    if state.implementation_plan_target_files:
        for file_path in state.implementation_plan_target_files:
            lines.append(f"- `{file_path}`")
    else:
        lines.append("- pending")
    lines.append("")
    lines.append("### Plan Steps")
    lines.append("")
    if state.implementation_plan_steps:
        for step in state.implementation_plan_steps:
            lines.append(f"#### Step {step.get('step_number')}: {step.get('title')}")
            lines.append("")
            lines.append(step.get("description") or "No description provided.")
            lines.append("")
            lines.append("Target files:")
            target_files = step.get("target_files") or []
            if target_files:
                for file_path in target_files:
                    lines.append(f"- `{file_path}`")
            else:
                lines.append("- none")
            lines.append("")
            lines.append("Expected changes:")
            for item in step.get("expected_changes") or ["pending"]:
                lines.append(f"- {item}")
            lines.append("")
            lines.append("Test impact:")
            for item in step.get("test_impact") or ["pending"]:
                lines.append(f"- {item}")
            lines.append("")
            lines.append(f"Risk level: `{step.get('risk_level') or 'pending'}`")
            lines.append("")
    else:
        lines.append("- pending")
    lines.append("")
    lines.append("### Test Strategy")
    lines.append("")
    if state.implementation_plan_test_strategy:
        for item in state.implementation_plan_test_strategy:
            lines.append(f"- {item}")
    else:
        lines.append("- pending")
    lines.append("")
    lines.append("### Implementation Plan Risks")
    lines.append("")
    if state.implementation_plan_risks:
        for item in state.implementation_plan_risks:
            lines.append(f"- {item}")
    else:
        lines.append("- pending")
    lines.append("")
    lines.append("### Implementation Plan Assumptions")
    lines.append("")
    if state.implementation_plan_assumptions:
        for item in state.implementation_plan_assumptions:
            lines.append(f"- {item}")
    else:
        lines.append("- pending")
    lines.append("")
    lines.append("### Legacy Flat Plan")
    lines.append("")
    if state.implementation_plan:
        for index, step in enumerate(state.implementation_plan, start=1):
            lines.append(f"{index}. {step}")
    else:
        lines.append("pending")
    lines.append("")
    lines.append("## Dev Agent Context")
    lines.append("")
    lines.append(f"- Status: `{state.dev_context_status or 'pending'}`")
    lines.append("")
    lines.append("### Selected Files")
    lines.append("")
    if state.dev_context_selected_files:
        for file_path in state.dev_context_selected_files:
            lines.append(f"- `{file_path}`")
    else:
        lines.append("- pending")
    lines.append("")
    lines.append("### Related Tests")
    lines.append("")
    if state.dev_context_related_tests:
        for file_path in state.dev_context_related_tests:
            lines.append(f"- `{file_path}`")
    else:
        lines.append("- pending")
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

    lines.append("## CI Status")
    lines.append("")
    lines.append(f"- Status: `{state.ci_status or 'pending'}`")
    lines.append(f"- Check Count: `{state.ci_check_count}`")
    lines.append("")
    lines.append("### CI Summary")
    lines.append("")
    lines.append(state.ci_summary or "pending")
    lines.append("")

    lines.append("### CI Error")
    lines.append("")
    lines.append(state.ci_error or "pending")
    lines.append("")

    lines.append("### Failed Checks")
    lines.append("")
    if state.ci_failed_checks:
        for check in state.ci_failed_checks:
            lines.append(f"- {check}")
    else:
        lines.append("- pending")
    lines.append("")

    lines.append("### Pending Checks")
    lines.append("")
    if state.ci_pending_checks:
        for check in state.ci_pending_checks:
            lines.append(f"- {check}")
    else:
        lines.append("- pending")
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

    lines.append("## MVP Release Candidate")
    lines.append("")
    lines.append(f"- Status: `{state.mvp_release_status or 'pending'}`")
    lines.append(f"- Release Notes: `{state.mvp_release_notes_path or 'pending'}`")
    lines.append("")
    lines.append("### MVP Release Checklist")
    lines.append("")
    if state.mvp_release_checklist:
        for item in state.mvp_release_checklist:
            lines.append(f"- [ ] {item}")
    else:
        lines.append("- pending")
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

    lines.append("## Controlled Fix Patch Loop")
    lines.append("")
    lines.append(f"- Attempt Count: `{state.fix_patch_attempt_count}`")
    lines.append(f"- Max Attempts: `{state.fix_patch_max_attempts}`")
    lines.append(f"- Status: `{state.fix_patch_status or 'pending'}`")
    lines.append("")
    lines.append("### Fix Patch Summary")
    lines.append("")
    lines.append(state.fix_patch_summary or "pending")
    lines.append("")
    lines.append("### Fix Patch Target Files")
    lines.append("")
    if state.fix_patch_target_files:
        for file_path in state.fix_patch_target_files:
            lines.append(f"- `{file_path}`")
    else:
        lines.append("- pending")
    lines.append("")
    lines.append("### Fix Patch Last Error")
    lines.append("")
    lines.append(state.fix_patch_last_error or "pending")
    lines.append("")

    lines.append("## Release Readiness")
    lines.append("")
    lines.append(f"- Status: `{state.readiness_status or 'pending'}`")
    lines.append(f"- Risk Level: `{state.readiness_risk_level or 'pending'}`")
    lines.append("")
    lines.append("### Readiness Summary")
    lines.append("")
    lines.append(state.readiness_summary or "pending")
    lines.append("")

    lines.append("### Blockers")
    lines.append("")
    if state.readiness_blockers:
        for blocker in state.readiness_blockers:
            lines.append(f"- {blocker}")
    else:
        lines.append("- pending")
    lines.append("")

    lines.append("### Warnings")
    lines.append("")
    if state.readiness_warnings:
        for warning in state.readiness_warnings:
            lines.append(f"- {warning}")
    else:
        lines.append("- pending")
    lines.append("")

    lines.append("### Readiness Next Actions")
    lines.append("")
    if state.readiness_next_actions:
        for action in state.readiness_next_actions:
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
