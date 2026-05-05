from pathlib import Path

from app.services.service_result import ServiceResult
from app.state_store import load_state, save_state
from app.tools.approval_request_tools import (
    apply_approval_request_to_state,
    build_approval_request,
)
from app.tools.markdown_tracking_tools import update_delivery_markdown


def get_or_build_approval_status(repo_path: Path) -> ServiceResult:
    state = load_state(repo_path)

    if not state.pending_approval and not state.pending_action:
        return ServiceResult(
            status="none",
            message="No pending approval.",
        )

    action = state.pending_action or state.approval_request_action

    if action and not state.approval_request_action:
        request = build_approval_request(repo_path, state, action)
        apply_approval_request_to_state(state, request)
        save_state(state)
        update_delivery_markdown(state)

    return ServiceResult(
        status="pending",
        message="Pending approval request found.",
        details={
            "action": state.approval_request_action or state.pending_action,
            "risk_level": state.approval_request_risk_level,
            "reason": state.approval_request_reason,
            "command": state.approval_request_command,
            "expected_result": state.approval_request_expected_result,
            "rollback_note": state.approval_request_rollback_note,
            "affected_files": ", ".join(state.approval_request_affected_files),
        },
    )
