from pathlib import Path

from app.schemas.delivery_state import DeliveryState
from app.schemas.release_readiness import ReleaseReadinessResult
from app.tools.patch_file_tools import get_changed_files


def has_completed(state: DeliveryState, step: str) -> bool:
    return step in state.completed_steps


def calculate_risk_level(blockers: list[str], warnings: list[str]) -> str:
    if blockers:
        return "high"

    if len(warnings) >= 3:
        return "medium"

    if warnings:
        return "low"

    return "low"


def determine_readiness_status(blockers: list[str], warnings: list[str]) -> str:
    if blockers:
        return "blocked"

    if warnings:
        return "needs_review"

    return "ready"


def build_next_actions(status: str, blockers: list[str], warnings: list[str]) -> list[str]:
    if status == "ready":
        return [
            "Proceed with the next approved delivery workflow step.",
            "Keep DELIVERY.md and state.json updated after the next action.",
        ]

    actions: list[str] = []

    if blockers:
        actions.append("Resolve blockers before commit, push, or PR actions.")

    if warnings:
        actions.append("Review warnings and decide whether they are acceptable for this MVP stage.")

    if any("test" in item.lower() for item in blockers + warnings):
        actions.append("Run or fix tests before continuing.")

    if any("approval" in item.lower() for item in blockers + warnings):
        actions.append("Request explicit approval before the risky action.")

    if not actions:
        actions.append("Review DELIVERY.md and state.json before continuing.")

    return actions


def evaluate_release_readiness(repo_path: Path, state: DeliveryState) -> ReleaseReadinessResult:
    blockers: list[str] = []
    warnings: list[str] = []

    changed_files = get_changed_files(repo_path)

    if not state.original_request.strip():
        blockers.append("Original request is missing.")

    if not state.github_issue_url:
        warnings.append("GitHub issue URL is missing.")

    if not state.branch_name:
        warnings.append("Feature branch is not recorded in state.")

    if state.pending_approval and state.pending_action:
        blockers.append(f"Workflow is waiting for approval: {state.pending_action}.")

    if state.last_error:
        warnings.append(f"Last recorded error exists: {state.last_error}")

    if not has_completed(state, "apply_patch"):
        blockers.append("Patch has not been applied yet.")

    if state.test_status == "failed":
        blockers.append("Tests are currently failing.")

        if not has_completed(state, "analyze_test_failure"):
            warnings.append("Test failure has not been analyzed yet.")

    elif state.test_status == "passed":
        pass

    elif state.test_status == "not_detected":
        warnings.append("No test command was detected.")

    elif state.test_status is None:
        warnings.append("Tests have not been run or recorded.")

    if has_completed(state, "run_tests") and state.test_status != "passed":
        blockers.append("Test step completed without passing status.")

    if not state.commit_message and not state.commit_hash:
        warnings.append("Commit message has not been generated yet.")

    if state.commit_message and not state.commit_hash:
        warnings.append("Commit message exists, but changes have not been committed yet.")

    if state.commit_hash and not has_completed(state, "commit_changes"):
        warnings.append("Commit hash exists, but commit_changes step is not marked completed.")

    if has_completed(state, "commit_changes") and not state.commit_hash:
        blockers.append("Commit step is marked completed, but commit hash is missing.")

    if has_completed(state, "push_branch") and not state.pushed_branch:
        warnings.append("Push step is marked completed, but pushed branch is missing.")

    if has_completed(state, "open_draft_pr") and not state.pr_url:
        warnings.append("Draft PR step is marked completed, but PR URL is missing.")

    if not changed_files and not state.commit_hash:
        warnings.append("No current changed files detected and no commit hash recorded.")

    if state.patch_risk_level == "high":
        warnings.append("Patch risk level is high.")

    if state.security_notes:
        warnings.append("Security notes exist and should be reviewed.")

    if state.policy_profile == "production_repo":
        if state.test_status != "passed":
            blockers.append("Production policy requires passing tests.")

        if not state.github_issue_url:
            blockers.append("Production policy requires a GitHub issue.")

        if state.pending_approval and state.pending_action:
            blockers.append(
                f"Production policy cannot proceed while approval is pending: {state.pending_action}."
            )

    elif state.policy_profile == "sandbox":
        warnings.append("Sandbox policy profile is active. Do not treat this as production evidence.")

    status = determine_readiness_status(blockers, warnings)
    risk_level = calculate_risk_level(blockers, warnings)

    summary = (
        f"Release readiness status is `{status}` with `{risk_level}` risk. "
        f"Blockers: {len(blockers)}. Warnings: {len(warnings)}."
    )

    return ReleaseReadinessResult(
        status=status,
        risk_level=risk_level,
        summary=summary,
        blockers=blockers,
        warnings=warnings,
        next_actions=build_next_actions(status, blockers, warnings),
    )


def apply_readiness_result_to_state(
    state: DeliveryState,
    result: ReleaseReadinessResult,
) -> None:
    state.readiness_status = result.status
    state.readiness_risk_level = result.risk_level
    state.readiness_summary = result.summary
    state.readiness_blockers = result.blockers
    state.readiness_warnings = result.warnings
    state.readiness_next_actions = result.next_actions
    state.mark_completed("release_readiness_check")
