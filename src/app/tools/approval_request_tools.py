from pathlib import Path

from app.schemas.approval_request import ApprovalRequest
from app.schemas.delivery_state import DeliveryState
from app.tools.patch_file_tools import get_changed_files


def get_best_known_files(repo_path: Path, state: DeliveryState) -> list[str]:
    candidates: list[str] = []

    for file_path in (
        state.patch_affected_files
        + state.committed_files
        + state.changed_files
        + state.likely_files
    ):
        if file_path and file_path not in candidates:
            candidates.append(file_path)

    if candidates:
        return candidates

    try:
        return get_changed_files(repo_path)
    except Exception:
        return []


def build_approval_request(
    repo_path: Path,
    state: DeliveryState,
    action: str,
) -> ApprovalRequest:
    affected_files = get_best_known_files(repo_path, state)
    policy_profile = getattr(state, "policy_profile", "personal_repo")

    if action == "apply_patch":
        return ApprovalRequest(
            action=action,
            reason="Apply the prepared patch to the working tree.",
            risk_level=state.patch_risk_level or "medium",
            affected_files=affected_files,
            command="uv run deliveryops apply-patch --repo .",
            expected_result="The generated patch is applied to the local working tree.",
            rollback_note="Use `git restore <file>` for modified files, or inspect rejected/generated patches before retrying.",
            policy_profile=policy_profile,
        )

    if action == "git_commit":
        return ApprovalRequest(
            action=action,
            reason="Create a git commit for the approved local changes.",
            risk_level="medium",
            affected_files=affected_files,
            command="uv run deliveryops commit --repo .",
            expected_result="A new git commit is created on the current feature branch.",
            rollback_note="Use `git reset --soft HEAD~1` to undo the commit while keeping changes staged.",
            policy_profile=policy_profile,
        )

    if action == "git_push":
        return ApprovalRequest(
            action=action,
            reason="Push the current feature branch to the configured remote.",
            risk_level="high" if policy_profile == "production_repo" else "medium",
            affected_files=affected_files,
            command="uv run deliveryops push --repo .",
            expected_result="The current feature branch is pushed to the remote repository.",
            rollback_note="If needed, delete the remote branch with `git push origin --delete <branch>`. Be careful if others may use it.",
            policy_profile=policy_profile,
        )

    if action == "create_draft_pull_request":
        return ApprovalRequest(
            action=action,
            reason="Open a draft pull request for the pushed feature branch.",
            risk_level="high" if policy_profile == "production_repo" else "medium",
            affected_files=affected_files,
            command="uv run deliveryops open-draft-pr --repo .",
            expected_result="A GitHub draft pull request is created from the feature branch into the base branch.",
            rollback_note="Close the draft PR manually or with GitHub CLI if it was opened by mistake.",
            policy_profile=policy_profile,
        )

    if action == "comment_progress":
        return ApprovalRequest(
            action=action,
            reason="Post a progress comment to the linked GitHub issue.",
            risk_level="low",
            affected_files=[],
            command="uv run deliveryops comment-progress --repo .",
            expected_result="A progress comment is added to the GitHub issue.",
            rollback_note="Delete or edit the GitHub issue comment manually if needed.",
            policy_profile=policy_profile,
        )

    return ApprovalRequest(
        action=action,
        reason=f"Approval is required before running action: {action}.",
        risk_level="medium",
        affected_files=affected_files,
        command=None,
        expected_result="The requested action will run after approval.",
        rollback_note="Review the action-specific result and use Git/GitHub rollback steps if needed.",
        policy_profile=policy_profile,
    )


def apply_approval_request_to_state(
    state: DeliveryState,
    request: ApprovalRequest,
) -> None:
    state.approval_request_action = request.action
    state.approval_request_reason = request.reason
    state.approval_request_risk_level = request.risk_level
    state.approval_request_affected_files = request.affected_files
    state.approval_request_command = request.command
    state.approval_request_expected_result = request.expected_result
    state.approval_request_rollback_note = request.rollback_note

    state.pending_action = request.action
    state.pending_approval = True
