from pathlib import Path

from app.schemas.delivery_state import DeliveryState
from app.schemas.workflow_decision import WorkflowDecision
from app.tools.workflow_resume_tools import determine_next_workflow_step


APPROVAL_REQUIRED_ACTIONS = {
    "apply_patch",
    "git_commit",
    "git_push",
    "create_draft_pull_request",
    "comment_progress",
}

SAFE_ACTIONS = {
    "detect_tests",
    "run_tests",
    "analyze_test_failure",
    "readiness_check",
    "generate_commit_message",
    "check_ci",
    "final_report",
}


class FeatureDeliveryWorkflow:
    """
    Central workflow orchestration boundary for DeliveryOps feature delivery.

    This starts as a thin orchestrator over the existing deterministic workflow
    tools so v0.2 can evolve toward Agno-based orchestration without changing
    current CLI behavior.
    """

    def __init__(self, repo_path: Path, state: DeliveryState):
        self.repo_path = repo_path
        self.state = state

    def determine_next_step(self) -> WorkflowDecision:
        decision = determine_next_workflow_step(self.repo_path, self.state)
        action = decision.next_action
        approval_action = action.removeprefix("approve_") if action else None
        requires_approval = bool(
            decision.status == "approval_required"
            or (action and action.startswith("approve_"))
            or approval_action in APPROVAL_REQUIRED_ACTIONS
            or action in APPROVAL_REQUIRED_ACTIONS
        )
        safe_to_run = bool(decision.safe_to_run and action in SAFE_ACTIONS)
        blockers: list[str] = []
        warnings: list[str] = []

        if decision.status == "blocked":
            blockers.append(decision.reason)

        if requires_approval:
            warnings.append(f"Action requires approval: {action}")

        return WorkflowDecision(
            status=decision.status,
            next_action=action,
            next_command=decision.next_command,
            reason=decision.reason,
            safe_to_run=safe_to_run,
            requires_approval=requires_approval,
            blockers=blockers,
            warnings=warnings,
            notes=decision.notes,
        )

    def can_auto_run_next_step(self) -> bool:
        decision = self.determine_next_step()

        return (
            decision.status == "ready"
            and decision.safe_to_run
            and not decision.requires_approval
            and not decision.blockers
        )

    def describe_current_position(self) -> str:
        decision = self.determine_next_step()

        if decision.next_action:
            return (
                f"Current step: {self.state.current_step}. "
                f"Next action: {decision.next_action}. "
                f"Reason: {decision.reason}"
            )

        return (
            f"Current step: {self.state.current_step}. "
            f"Workflow status: {decision.status}. "
            f"Reason: {decision.reason}"
        )
