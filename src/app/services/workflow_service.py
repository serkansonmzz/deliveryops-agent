from pathlib import Path

from app.services.service_result import ServiceResult
from app.state_store import load_state
from app.tools.auto_continue_tools import execute_safe_action
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


def run_auto_continue(repo_path: Path, max_steps: int = 5) -> ServiceResult:
    state = load_state(repo_path)
    executed_actions: list[str] = []
    warnings: list[str] = []

    for _ in range(max_steps):
        workflow = FeatureDeliveryWorkflow(repo_path, state)
        decision = workflow.determine_next_step()

        if decision.status == "completed":
            return ServiceResult(
                status="completed",
                message=decision.reason,
                details={
                    "executed_count": len(executed_actions),
                    "last_action": executed_actions[-1] if executed_actions else None,
                    "next_action": None,
                    "next_command": None,
                },
                warnings=warnings + decision.warnings + decision.notes,
            )

        if decision.status != "ready":
            status = (
                "stopped"
                if decision.status == "approval_required" or decision.requires_approval
                else decision.status
            )

            return ServiceResult(
                status=status,
                message=decision.reason,
                details={
                    "executed_count": len(executed_actions),
                    "last_action": executed_actions[-1] if executed_actions else None,
                    "next_action": decision.next_action,
                    "next_command": decision.next_command,
                    "safe_to_run": decision.safe_to_run,
                    "requires_approval": decision.requires_approval,
                },
                warnings=warnings + decision.warnings + decision.notes,
                errors=decision.blockers,
            )

        if not workflow.can_auto_run_next_step():
            return ServiceResult(
                status="stopped",
                message=decision.reason,
                details={
                    "executed_count": len(executed_actions),
                    "last_action": executed_actions[-1] if executed_actions else None,
                    "next_action": decision.next_action,
                    "next_command": decision.next_command,
                    "safe_to_run": decision.safe_to_run,
                    "requires_approval": decision.requires_approval,
                },
                warnings=warnings + decision.warnings + decision.notes,
                errors=decision.blockers,
            )

        if not decision.next_action:
            return ServiceResult(
                status="completed",
                message="No next action found.",
                details={"executed_count": len(executed_actions)},
                warnings=warnings,
            )

        execute_safe_action(repo_path, state, decision.next_action)
        executed_actions.append(decision.next_action)
        state = load_state(repo_path)

    workflow = FeatureDeliveryWorkflow(repo_path, state)
    decision = workflow.determine_next_step()

    return ServiceResult(
        status="max_steps_reached",
        message="Auto-continue stopped after reaching the maximum number of steps.",
        details={
            "executed_count": len(executed_actions),
            "last_action": executed_actions[-1] if executed_actions else None,
            "next_action": decision.next_action,
            "next_command": decision.next_command,
        },
        warnings=warnings + decision.warnings + decision.notes,
    )
