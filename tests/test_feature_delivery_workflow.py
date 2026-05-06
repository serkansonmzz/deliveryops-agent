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


def test_workflow_describes_current_position(tmp_path: Path):
    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Test workflow orchestrator",
    )

    workflow = FeatureDeliveryWorkflow(tmp_path, state)
    description = workflow.describe_current_position()

    assert "Current step" in description
