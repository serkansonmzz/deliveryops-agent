from pathlib import Path

from app.schemas.approval_record import ApprovalRecord
from app.schemas.delivery_state import DeliveryState
from app.tools.approval_tools import append_approval_record
from app.tools.workflow_resume_tools import determine_next_workflow_step


def approve(repo_path: Path, state: DeliveryState, action: str) -> None:
    append_approval_record(
        repo_path,
        ApprovalRecord(
            request_id=state.request_id,
            action=action,
            decision="approved",
            reason="Test approval.",
        ),
    )


def test_continue_requires_patch_generation_when_no_patch_exists(tmp_path: Path):
    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Update README documentation",
    )

    decision = determine_next_workflow_step(tmp_path, state)

    assert decision.status == "ready"
    assert decision.next_action == "dev_generate_patch"
    assert "dev-generate-patch" in decision.next_command


def test_continue_requires_apply_patch_approval_when_patch_exists(tmp_path: Path):
    workspace = tmp_path / ".deliveryops"
    workspace.mkdir()
    (workspace / "generated.patch").write_text("patch", encoding="utf-8")

    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Update README documentation",
    )

    decision = determine_next_workflow_step(tmp_path, state)

    assert decision.status == "approval_required"
    assert decision.next_action == "approve_apply_patch"
    assert "apply_patch" in decision.next_command


def test_continue_runs_apply_patch_after_approval(tmp_path: Path):
    workspace = tmp_path / ".deliveryops"
    workspace.mkdir()
    (workspace / "generated.patch").write_text("patch", encoding="utf-8")

    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Update README documentation",
    )

    approve(tmp_path, state, "apply_patch")

    decision = determine_next_workflow_step(tmp_path, state)

    assert decision.status == "ready"
    assert decision.next_action == "apply_patch"
    assert "apply-patch" in decision.next_command


def test_continue_detects_tests_after_patch_applied(tmp_path: Path):
    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Update README documentation",
    )
    state.mark_completed("apply_patch")

    decision = determine_next_workflow_step(tmp_path, state)

    assert decision.status == "ready"
    assert decision.next_action == "detect_tests"
    assert "detect-tests" in decision.next_command


def test_continue_generates_commit_message_after_tests(tmp_path: Path):
    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Update README documentation",
    )
    state.mark_completed("apply_patch")
    state.mark_completed("detect_tests")
    state.test_status = "not_detected"

    decision = determine_next_workflow_step(tmp_path, state)

    assert decision.status == "ready"
    assert decision.next_action == "generate_commit_message"
    assert "generate-commit-message" in decision.next_command


def test_continue_requires_git_commit_approval(tmp_path: Path):
    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Update README documentation",
    )
    state.mark_completed("apply_patch")
    state.mark_completed("detect_tests")
    state.mark_completed("generate_commit_message")

    decision = determine_next_workflow_step(tmp_path, state)

    assert decision.status == "approval_required"
    assert decision.next_action == "approve_git_commit"
    assert "git_commit" in decision.next_command


def test_continue_runs_commit_after_approval(tmp_path: Path):
    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Update README documentation",
    )
    state.mark_completed("apply_patch")
    state.mark_completed("detect_tests")
    state.mark_completed("generate_commit_message")

    approve(tmp_path, state, "git_commit")

    decision = determine_next_workflow_step(tmp_path, state)

    assert decision.status == "ready"
    assert decision.next_action == "git_commit"
    assert "commit" in decision.next_command


def test_continue_completed_workflow(tmp_path: Path):
    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Update README documentation",
    )

    for step in [
        "apply_patch",
        "detect_tests",
        "generate_commit_message",
        "commit_changes",
        "push_branch",
        "open_draft_pr",
        "comment_progress",
        "generate_final_report",
    ]:
        state.mark_completed(step)

    decision = determine_next_workflow_step(tmp_path, state)

    assert decision.status == "completed"
    assert decision.next_action is None