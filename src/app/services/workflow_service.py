from pathlib import Path

from app.services.service_result import ServiceResult
from app.state_store import load_state
from app.workflows.feature_delivery_workflow import FeatureDeliveryWorkflow


def get_workflow_status(repo_path: Path) -> ServiceResult:
    state = load_state(repo_path)
    workflow = FeatureDeliveryWorkflow(repo_path, state)
    decision = workflow.determine_next_step()

    return ServiceResult(
        status=decision.status,
        message=decision.reason,
        details={
            "current_step": state.current_step,
            "next_action": decision.next_action,
            "next_command": decision.next_command,
            "safe_to_run": decision.safe_to_run,
            "requires_approval": decision.requires_approval,
        },
        warnings=decision.warnings + decision.notes,
        errors=decision.blockers,
    )
