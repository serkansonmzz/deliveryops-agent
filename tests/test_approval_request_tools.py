from pathlib import Path

from app.schemas.delivery_state import DeliveryState
from app.tools.approval_request_tools import (
    build_approval_request,
    apply_approval_request_to_state,
)


def test_build_apply_patch_approval_request(tmp_path: Path):
    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Update README documentation",
        patch_affected_files=["README.md"],
        patch_risk_level="medium",
    )

    request = build_approval_request(tmp_path, state, "apply_patch")

    assert request.action == "apply_patch"
    assert request.risk_level == "medium"
    assert "README.md" in request.affected_files
    assert "apply-patch" in request.command


def test_build_git_commit_approval_request(tmp_path: Path):
    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Update README documentation",
        changed_files=["README.md"],
    )

    request = build_approval_request(tmp_path, state, "git_commit")

    assert request.action == "git_commit"
    assert request.risk_level == "medium"
    assert "commit" in request.command
    assert "git reset --soft HEAD~1" in request.rollback_note


def test_build_git_push_approval_request_uses_high_risk_for_production(tmp_path: Path):
    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Update README documentation",
        policy_profile="production_repo",
        committed_files=["README.md"],
    )

    request = build_approval_request(tmp_path, state, "git_push")

    assert request.action == "git_push"
    assert request.risk_level == "high"


def test_apply_approval_request_to_state(tmp_path: Path):
    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Update README documentation",
        changed_files=["README.md"],
    )

    request = build_approval_request(tmp_path, state, "git_commit")
    apply_approval_request_to_state(state, request)

    assert state.pending_action == "git_commit"
    assert state.pending_approval is True
    assert state.approval_request_action == "git_commit"
    assert state.approval_request_affected_files == ["README.md"]
