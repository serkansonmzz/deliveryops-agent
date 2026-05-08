from pathlib import Path

from app.schemas.delivery_state import DeliveryState
from app.workflows.feature_delivery_workflow import FeatureDeliveryWorkflow


def test_workflow_marks_approval_action_as_requires_approval(tmp_path: Path):
    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Test workflow orchestrator",
        pending_action="apply_patch",
        pending_approval=True,
    )

    workflow = FeatureDeliveryWorkflow(tmp_path, state)
    decision = workflow.determine_next_step()

    assert decision.requires_approval is True
    assert decision.safe_to_run is False
    assert workflow.can_auto_run_next_step() is False


def test_workflow_describes_current_position(tmp_path: Path):
    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Test workflow orchestrator",
    )

    workflow = FeatureDeliveryWorkflow(tmp_path, state)
    description = workflow.describe_current_position()

    assert "Current step" in description


def test_workflow_does_not_auto_run_llm_patch_generation(tmp_path: Path, monkeypatch):
    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Test LLM action gate",
    )

    class FakeDecision:
        status = "ready"
        next_action = "generate_fix_patch"
        next_command = "uv run deliveryops generate-fix-patch --repo ."
        reason = "Generate a controlled fix patch."
        safe_to_run = True
        notes = []

    monkeypatch.setattr(
        "app.workflows.feature_delivery_workflow.determine_next_workflow_step",
        lambda repo_path, state: FakeDecision(),
    )

    workflow = FeatureDeliveryWorkflow(tmp_path, state)
    decision = workflow.determine_next_step()

    assert decision.safe_to_run is False
    assert decision.requires_approval is False
    assert workflow.can_auto_run_next_step() is False
    assert any("manual trigger" in warning for warning in decision.warnings)


def test_workflow_does_not_auto_run_implementation_plan(tmp_path: Path, monkeypatch):
    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Test planner action gate",
    )

    class FakeDecision:
        status = "ready"
        next_action = "implementation_plan"
        next_command = "uv run deliveryops implementation-plan --repo ."
        reason = "Generate a structured implementation plan."
        safe_to_run = True
        notes = []

    monkeypatch.setattr(
        "app.workflows.feature_delivery_workflow.determine_next_workflow_step",
        lambda repo_path, state: FakeDecision(),
    )

    workflow = FeatureDeliveryWorkflow(tmp_path, state)
    decision = workflow.determine_next_step()

    assert decision.safe_to_run is False
    assert decision.requires_approval is False
    assert workflow.can_auto_run_next_step() is False
    assert any("manual trigger" in warning for warning in decision.warnings)
