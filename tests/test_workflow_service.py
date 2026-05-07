from pathlib import Path
import subprocess

from app.schemas.delivery_state import DeliveryState
from app.services.workflow_service import get_workflow_status, run_auto_continue
from app.state_store import ensure_workspace, save_state


def init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, stdout=subprocess.PIPE)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=path,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=path,
        check=True,
    )


def test_get_workflow_status_returns_service_result(tmp_path: Path):
    init_git_repo(tmp_path)
    ensure_workspace(tmp_path)
    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Test workflow service",
    )
    save_state(state)

    result = get_workflow_status(tmp_path)

    assert result.status
    assert "current_step" in result.details
    assert "safe_to_run" in result.details
    assert "requires_approval" in result.details


def test_run_auto_continue_stops_before_approval_required_action(tmp_path: Path):
    init_git_repo(tmp_path)
    ensure_workspace(tmp_path)
    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Test auto continue approval stop",
        pending_action="apply_patch",
        pending_approval=True,
    )
    save_state(state)

    result = run_auto_continue(tmp_path, max_steps=3)

    assert result.status == "stopped"
    assert result.details.get("next_action") == "approve_apply_patch"
    assert result.details.get("requires_approval") is True
    assert result.details.get("executed_count") == 0


def test_run_auto_continue_respects_max_steps(monkeypatch, tmp_path: Path):
    init_git_repo(tmp_path)
    ensure_workspace(tmp_path)
    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Test max steps",
    )
    save_state(state)
    calls = {"count": 0}

    class FakeDecision:
        status = "ready"
        next_action = "detect_tests"
        next_command = "uv run deliveryops detect-tests --repo ."
        reason = "Detect tests."
        safe_to_run = True
        requires_approval = False
        blockers = []
        warnings = []
        notes = []

    class FakeWorkflow:
        def __init__(self, repo_path, state):
            pass

        def determine_next_step(self):
            return FakeDecision()

        def can_auto_run_next_step(self):
            return True

    def fake_execute_safe_action(repo_path, state, action):
        calls["count"] += 1
        save_state(state)

    monkeypatch.setattr("app.services.workflow_service.FeatureDeliveryWorkflow", FakeWorkflow)
    monkeypatch.setattr("app.services.workflow_service.execute_safe_action", fake_execute_safe_action)

    result = run_auto_continue(tmp_path, max_steps=2)

    assert result.status == "max_steps_reached"
    assert calls["count"] == 2
