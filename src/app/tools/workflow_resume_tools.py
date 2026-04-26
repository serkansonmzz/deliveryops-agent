from pathlib import Path

from app.schemas.continue_decision import ContinueDecision
from app.schemas.delivery_state import DeliveryState
from app.tools.approval_tools import has_approved_action


def build_deliveryops_command(command: str, repo: str = ".") -> str:
    return f"uv run deliveryops {command} --repo {repo}"


def build_approval_command(action: str, repo: str = ".") -> str:
    return (
        f'uv run deliveryops approve --repo {repo} '
        f'--action {action} '
        f'--reason "Approved by workflow operator."'
    )


def has_step(state: DeliveryState, step: str) -> bool:
    return step in state.completed_steps


def determine_next_workflow_step(repo_path: Path, state: DeliveryState) -> ContinueDecision:
    generated_patch_path = repo_path / ".deliveryops" / "generated.patch"

    if state.pending_approval and state.pending_action:
        return ContinueDecision(
            status="blocked",
            next_action=f"approve_{state.pending_action}",
            next_command=build_approval_command(state.pending_action),
            reason=f"Workflow is waiting for approval: {state.pending_action}.",
            safe_to_run=False,
            notes=["Approval is required before the workflow can continue."],
        )

    if not has_step(state, "apply_patch"):
        if not generated_patch_path.exists():
            return ContinueDecision(
                status="ready",
                next_action="dev_generate_patch",
                next_command=build_deliveryops_command("dev-generate-patch"),
                reason="No generated patch was found. Generate a patch before applying changes.",
                safe_to_run=True,
                notes=[
                    "Use dev-generate-patch for Agno-based patch generation.",
                    "Use generate-patch if you want deterministic patch generation.",
                ],
            )

        if has_approved_action(repo_path, state.request_id, "apply_patch"):
            return ContinueDecision(
                status="ready",
                next_action="apply_patch",
                next_command=build_deliveryops_command("apply-patch"),
                reason="Patch exists and apply_patch has been approved.",
                safe_to_run=False,
                notes=["This command modifies files, so run it intentionally."],
            )

        return ContinueDecision(
            status="approval_required",
            next_action="approve_apply_patch",
            next_command=build_approval_command("apply_patch"),
            reason="A generated patch exists, but apply_patch has not been approved yet.",
            safe_to_run=False,
        )

    if not has_step(state, "detect_tests"):
        return ContinueDecision(
            status="ready",
            next_action="detect_tests",
            next_command=build_deliveryops_command("detect-tests"),
            reason="Patch has been applied. Detect the test command next.",
            safe_to_run=True,
        )

    if state.test_command and not has_step(state, "run_tests"):
        return ContinueDecision(
            status="ready",
            next_action="run_tests",
            next_command=build_deliveryops_command("run-tests"),
            reason="A safe test command was detected. Run tests before generating the commit message.",
            safe_to_run=True,
        )

    if state.test_status == "failed":
        return ContinueDecision(
            status="blocked",
            next_action=None,
            next_command=None,
            reason="Tests failed. Fix the issue before continuing to commit.",
            safe_to_run=False,
            notes=["Check DELIVERY.md for the test summary."],
        )

    if not has_step(state, "generate_commit_message"):
        return ContinueDecision(
            status="ready",
            next_action="generate_commit_message",
            next_command=build_deliveryops_command("generate-commit-message"),
            reason="Patch has been applied. Generate a commit message next.",
            safe_to_run=True,
        )

    if not has_step(state, "commit_changes"):
        if has_approved_action(repo_path, state.request_id, "git_commit"):
            return ContinueDecision(
                status="ready",
                next_action="git_commit",
                next_command=build_deliveryops_command("commit"),
                reason="Commit message exists and git_commit has been approved.",
                safe_to_run=False,
                notes=["This command creates a real git commit."],
            )

        return ContinueDecision(
            status="approval_required",
            next_action="approve_git_commit",
            next_command=build_approval_command("git_commit"),
            reason="Commit message was generated, but git_commit has not been approved yet.",
            safe_to_run=False,
        )

    if not has_step(state, "push_branch"):
        if has_approved_action(repo_path, state.request_id, "git_push"):
            return ContinueDecision(
                status="ready",
                next_action="git_push",
                next_command=build_deliveryops_command("push"),
                reason="Commit exists and git_push has been approved.",
                safe_to_run=False,
                notes=["This command pushes the current feature branch to remote."],
            )

        return ContinueDecision(
            status="approval_required",
            next_action="approve_git_push",
            next_command=build_approval_command("git_push"),
            reason="Commit exists, but git_push has not been approved yet.",
            safe_to_run=False,
        )

    if not has_step(state, "open_draft_pr"):
        if has_approved_action(repo_path, state.request_id, "create_draft_pull_request"):
            return ContinueDecision(
                status="ready",
                next_action="open_draft_pr",
                next_command=build_deliveryops_command("open-draft-pr"),
                reason="Branch was pushed and draft PR creation has been approved.",
                safe_to_run=False,
                notes=["This command creates a real GitHub draft PR."],
            )

        return ContinueDecision(
            status="approval_required",
            next_action="approve_create_draft_pull_request",
            next_command=build_approval_command("create_draft_pull_request"),
            reason="Branch was pushed, but draft PR creation has not been approved yet.",
            safe_to_run=False,
        )

    if not has_step(state, "comment_progress"):
        return ContinueDecision(
            status="ready",
            next_action="comment_progress",
            next_command=build_deliveryops_command("comment-progress"),
            reason="Draft PR exists. Post a progress comment to the GitHub issue next.",
            safe_to_run=False,
            notes=["This command posts a real GitHub issue comment."],
        )

    if not has_step(state, "generate_final_report"):
        return ContinueDecision(
            status="ready",
            next_action="final_report",
            next_command=build_deliveryops_command("final-report"),
            reason="Progress was commented. Generate the final delivery report next.",
            safe_to_run=True,
        )

    return ContinueDecision(
        status="completed",
        next_action=None,
        next_command=None,
        reason="Workflow appears to be complete.",
        safe_to_run=False,
        notes=["No next action is required."],
    )