from pathlib import Path

from app.schemas.delivery_state import DeliveryState
from app.schemas.fix_patch_attempt import FixPatchAttempt
from app.tools.agent_patch_tools import generate_patch_with_agent
from app.tools.approval_request_tools import (
    build_approval_request,
    apply_approval_request_to_state,
)


def can_generate_fix_patch(state: DeliveryState) -> tuple[bool, str]:
    if state.test_status != "failed" and state.ci_status != "failed":
        return False, "No failed test or CI status found."

    if "analyze_test_failure" not in state.completed_steps and state.test_status == "failed":
        return False, "Test failure must be analyzed before generating a fix patch."

    if state.fix_patch_attempt_count >= state.fix_patch_max_attempts:
        return False, "Maximum fix patch attempts reached."

    return True, "Fix patch generation is allowed."


def enrich_state_for_fix_patch(state: DeliveryState) -> None:
    """
    Reuses the existing Dev Agent patch generator by making the current request
    more specific to the failure recovery context.
    """
    failure_context = "\n".join(
        [
            "Fix the current failed delivery workflow.",
            "",
            f"Original request: {state.original_request}",
            f"Test status: {state.test_status}",
            f"CI status: {state.ci_status}",
            f"Failure category: {state.test_failure_category}",
            "",
            "Failure summary:",
            state.test_failure_analysis_summary or state.test_summary or "not available",
            "",
            "Likely causes:",
            "\n".join(f"- {cause}" for cause in state.test_failure_likely_causes)
            or "- not available",
            "",
            "Next actions:",
            "\n".join(f"- {action}" for action in state.test_failure_next_actions)
            or "- not available",
            "",
            "Generate the smallest possible unified diff patch to fix the failing tests.",
            "Do not perform unrelated refactors.",
            "Do not modify secrets or environment files.",
        ]
    )

    state.original_request = failure_context

    if state.changed_files:
        state.likely_files = state.changed_files
    elif state.committed_files:
        state.likely_files = state.committed_files


def generate_controlled_fix_patch(repo_path: Path, state: DeliveryState) -> FixPatchAttempt:
    allowed, reason = can_generate_fix_patch(state)

    if not allowed:
        raise RuntimeError(reason)

    state.fix_patch_attempt_count += 1

    original_request = state.original_request
    original_likely_files = list(state.likely_files)

    try:
        enrich_state_for_fix_patch(state)

        patch_path = generate_patch_with_agent(repo_path, state)

        if patch_path is None:
            state.fix_patch_status = "not_generated"
            state.fix_patch_last_error = "Dev Agent did not generate a fix patch."

            return FixPatchAttempt(
                attempt_number=state.fix_patch_attempt_count,
                status="not_generated",
                summary="Dev Agent did not generate a fix patch.",
                target_files=state.likely_files,
                error=state.fix_patch_last_error,
            )

        state.fix_patch_status = "generated"
        state.fix_patch_summary = "A controlled fix patch was generated from failure analysis."
        state.fix_patch_target_files = state.likely_files

        approval_request = build_approval_request(repo_path, state, "apply_patch")
        approval_request.reason = (
            "Apply the controlled fix patch generated from test/CI failure analysis."
        )
        approval_request.risk_level = "medium"
        approval_request.expected_result = (
            "The fix patch is applied to the local working tree so tests can be re-run."
        )
        approval_request.rollback_note = (
            "Use `git restore <file>` to discard the fix patch if it is not acceptable."
        )

        apply_approval_request_to_state(state, approval_request)

        return FixPatchAttempt(
            attempt_number=state.fix_patch_attempt_count,
            status="generated",
            summary=state.fix_patch_summary,
            target_files=state.fix_patch_target_files,
            generated_patch_path=str(patch_path.relative_to(repo_path)),
        )

    except Exception as exc:
        state.fix_patch_status = "failed"
        state.fix_patch_last_error = str(exc)

        return FixPatchAttempt(
            attempt_number=state.fix_patch_attempt_count,
            status="failed",
            summary="Fix patch generation failed.",
            target_files=state.likely_files,
            rejected_patch_path=".deliveryops/rejected.patch",
            error=str(exc),
        )

    finally:
        state.original_request = original_request
        state.likely_files = original_likely_files
