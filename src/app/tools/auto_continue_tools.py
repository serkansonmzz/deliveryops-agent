from pathlib import Path

from app.schemas.auto_continue_result import AutoContinueResult
from app.schemas.delivery_state import DeliveryState
from app.state_store import save_state
from app.tools.commit_message_tools import build_commit_message_spec
from app.tools.delivery_report_tools import build_final_report, write_final_report
from app.tools.markdown_tracking_tools import update_delivery_markdown
from app.tools.test_tools import detect_test_command, run_safe_test_command
from app.tools.workflow_resume_tools import determine_next_workflow_step
from app.tools.test_failure_analysis_tools import analyze_test_failure
from app.tools.release_judge_tools import (
    evaluate_release_readiness,
    apply_readiness_result_to_state,
)

SAFE_AUTO_ACTIONS = {
    "detect_tests",
    "run_tests",
    "analyze_test_failure",
    "readiness_check",
    "generate_commit_message",
    "final_report",
}


def execute_safe_action(repo_path: Path, state: DeliveryState, action: str) -> None:
    if action == "detect_tests":
        command = detect_test_command(repo_path)

        if command is None:
            state.test_status = "not_detected"
            state.test_command = None
            state.test_summary = "No known test command was detected."
        else:
            state.test_command = command
            state.test_status = "detected"
            state.test_summary = f"Detected test command: {command}"

        state.mark_completed("detect_tests")

        save_state(state)
        update_delivery_markdown(state)
        return

    if action == "run_tests":
        if not state.test_command:
            state.test_status = "not_detected"
            state.test_summary = "No test command is available to run."
            save_state(state)
            update_delivery_markdown(state)
            return

        result = run_safe_test_command(repo_path, state.test_command)

        state.test_status = result.status
        state.test_exit_code = result.exit_code
        state.test_output = "\n".join(
            part for part in [result.stdout, result.stderr] if part.strip()
        )
        state.test_summary = result.summary

        state.mark_completed("run_tests")

        save_state(state)
        update_delivery_markdown(state)
        return

    if action == "readiness_check":
        result = evaluate_release_readiness(repo_path, state)
        apply_readiness_result_to_state(state, result)

        save_state(state)
        update_delivery_markdown(state)
        return

    if action == "generate_commit_message":
        commit_spec = build_commit_message_spec(repo_path, state)

        if not commit_spec.changed_files:
            state.last_error = "No changed files detected. Commit message was not generated."
            save_state(state)
            update_delivery_markdown(state)
            return

        state.commit_message = commit_spec.subject
        state.commit_body = commit_spec.body
        state.commit_diff_summary = commit_spec.diff_summary
        state.commit_rationale = commit_spec.rationale
        state.changed_files = commit_spec.changed_files

        state.pending_action = "git_commit"
        state.pending_approval = True

        state.mark_completed("generate_commit_message")
        state.mark_completed("request_commit_approval")

        save_state(state)
        update_delivery_markdown(state)
        return

    if action == "final_report":
        report = build_final_report(state)
        report_path = write_final_report(repo_path, report)

        state.final_report_path = str(report_path.relative_to(repo_path))
        state.final_report_status = "generated"

        state.mark_completed("generate_final_report")

        save_state(state)
        update_delivery_markdown(state)
        return

    if action == "analyze_test_failure":
        if state.test_status != "failed":
            state.last_error = "No failed test run found to analyze."
            save_state(state)
            update_delivery_markdown(state)
            return

        analysis = analyze_test_failure(state)

        state.test_failure_category = analysis.category
        state.test_failure_analysis_summary = analysis.summary
        state.test_failure_likely_causes = analysis.likely_causes
        state.test_failure_next_actions = analysis.next_actions
        state.test_failure_risk_level = analysis.risk_level

        state.mark_completed("analyze_test_failure")

        save_state(state)
        update_delivery_markdown(state)
        return
    raise RuntimeError(f"Unsupported safe auto action: {action}")


def run_safe_auto_continue(
    repo_path: Path,
    state: DeliveryState,
    max_steps: int = 5,
) -> AutoContinueResult:
    executed_actions: list[str] = []

    for _ in range(max_steps):
        decision = determine_next_workflow_step(repo_path, state)

        if decision.status == "completed":
            return AutoContinueResult(
                executed_actions=executed_actions,
                stopped_at_action=None,
                stopped_reason="Workflow is already complete.",
                completed=True,
            )

        if decision.next_action not in SAFE_AUTO_ACTIONS:
            return AutoContinueResult(
                executed_actions=executed_actions,
                stopped_at_action=decision.next_action,
                stopped_reason=decision.reason,
                completed=False,
            )

        execute_safe_action(repo_path, state, decision.next_action)
        executed_actions.append(decision.next_action)

    return AutoContinueResult(
        executed_actions=executed_actions,
        stopped_at_action=None,
        stopped_reason="Maximum safe auto-continue steps reached.",
        completed=False,
    )