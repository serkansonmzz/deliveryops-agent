import uuid

import typer

from app.cli.common import console, resolve_repo_path
from app.schemas.delivery_state import DeliveryState
from app.services.agent_intake_service import run_intake_agent
from app.services.issue_spec_service import run_product_owner_agent
from app.state_store import ensure_workspace, load_state, save_state
from app.tools.approval_request_tools import (
    apply_approval_request_to_state,
    build_approval_request,
)
from app.tools.architecture_review_tools import (
    build_architecture_review,
    build_implementation_plan,
)
from app.tools.auto_continue_tools import run_safe_auto_continue
from app.tools.branch_name_tools import build_feature_branch_name
from app.tools.git_tools import (
    create_branch,
    ensure_git_repo,
    get_current_branch,
    get_git_status,
)
from app.tools.github_tools import create_github_issue
from app.tools.markdown_tracking_tools import update_delivery_markdown
from app.tools.patch_proposal_tools import build_patch_proposal
from app.tools.smoke_test_tools import run_local_smoke_test
from app.tools.workflow_resume_tools import determine_next_workflow_step


def register_workflow_commands(app: typer.Typer) -> None:
    @app.command()
    def init(
        repo: str = typer.Option(".", help="Path to the local repository."),
        request: str = typer.Option(
            "Initial DeliveryOps workspace setup.",
            help="Initial request text.",
        ),
    ):
        repo_path = resolve_repo_path(repo)
        ensure_git_repo(repo_path)

        request_id = f"req_{uuid.uuid4().hex[:8]}"

        state = DeliveryState(
            request_id=request_id,
            repo_path=str(repo_path),
            original_request=request,
        )

        ensure_workspace(repo_path)
        state.mark_completed("initialize_workspace")
        save_state(state)
        update_delivery_markdown(state)

        console.print("[green]DeliveryOps workspace initialized.[/green]")
        console.print(f"Request ID: {request_id}")
        console.print(f"Workspace: {repo_path / '.deliveryops'}")

    @app.command()
    def status(repo: str = typer.Option(".", help="Path to the local repository.")):
        repo_path = resolve_repo_path(repo)
        state = load_state(repo_path)

        console.print("[bold]DeliveryOps Status[/bold]")
        console.print(f"Request ID: {state.request_id}")
        console.print(f"Current Step: {state.current_step}")
        console.print(f"Pending Approval: {state.pending_approval}")
        console.print(f"Pending Action: {state.pending_action or 'none'}")
        console.print(f"Completed Steps: {', '.join(state.completed_steps) or 'none'}")

    @app.command("continue")
    def continue_workflow_command(
        repo: str = typer.Option(".", help="Path to the local repository."),
    ):
        repo_path = resolve_repo_path(repo)
        state = load_state(repo_path)

        decision = determine_next_workflow_step(repo_path, state)

        console.print("[bold]DeliveryOps Continue[/bold]")
        console.print(f"Status: {decision.status}")
        console.print(f"Reason: {decision.reason}")

        if decision.next_action:
            console.print(f"Next Action: {decision.next_action}")

        if decision.next_command:
            console.print("")
            console.print("[bold]Next Command[/bold]")
            console.print(decision.next_command)

        if decision.notes:
            console.print("")
            console.print("[bold]Notes[/bold]")
            for note in decision.notes:
                console.print(f"- {note}")

    @app.command("auto-continue")
    def auto_continue_command(
        repo: str = typer.Option(".", help="Path to the local repository."),
        max_steps: int = typer.Option(5, help="Maximum number of safe workflow steps to execute."),
    ):
        repo_path = resolve_repo_path(repo)
        state = load_state(repo_path)

        result = run_safe_auto_continue(
            repo_path=repo_path,
            state=state,
            max_steps=max_steps,
        )

        console.print("[bold]DeliveryOps Auto-Continue[/bold]")

        if result.executed_actions:
            console.print("[green]Executed safe actions:[/green]")
            for action in result.executed_actions:
                console.print(f"- {action}")
        else:
            console.print("[yellow]No safe action was executed.[/yellow]")

        console.print("")
        console.print(f"Stopped Reason: {result.stopped_reason}")

        if result.stopped_at_action:
            console.print(f"Stopped At: {result.stopped_at_action}")

        if result.completed:
            console.print("[green]Workflow completed.[/green]")

    @app.command()
    def inspect(repo: str = typer.Option(".", help="Path to the local repository.")):
        repo_path = resolve_repo_path(repo)
        ensure_git_repo(repo_path)

        branch = get_current_branch(repo_path)
        status_text = get_git_status(repo_path)

        console.print("[bold]Repository Inspection[/bold]")
        console.print(f"Path: {repo_path}")
        console.print(f"Branch: {branch}")
        console.print("")
        console.print("[bold]Git Status[/bold]")
        console.print(status_text or "Working tree clean.")

    @app.command("smoke-test")
    def smoke_test_command(
        repo: str = typer.Option(".", help="Path to the local repository."),
    ):
        repo_path = resolve_repo_path(repo)

        workspace_path = (
            repo_path
            / ".deliveryops"
            / "smoke-tests"
            / f"smoke_{uuid.uuid4().hex[:8]}"
        )

        result = run_local_smoke_test(workspace_path)

        console.print("[green]DeliveryOps smoke test completed.[/green]")
        console.print(f"Passed: {result.passed}")
        console.print(f"Workspace: {result.workspace_path}")
        console.print(f"Repo: {result.repo_path}")
        console.print(f"Remote: {result.remote_path}")
        console.print(f"Branch: {result.branch_name}")
        console.print(f"Commit: {result.commit_hash}")
        console.print(f"Final report: {result.final_report_path}")

    @app.command()
    def run(
        repo: str = typer.Option(".", help="Path to the target local Git repository."),
        github_owner: str | None = typer.Option(None, help="GitHub repository owner."),
        github_repo: str | None = typer.Option(None, help="GitHub repository name."),
        request: str = typer.Option(..., help="Feature request to deliver."),
    ):
        repo_path = resolve_repo_path(repo)
        ensure_git_repo(repo_path)

        request_id = f"req_{uuid.uuid4().hex[:8]}"

        state = DeliveryState(
            request_id=request_id,
            repo_path=str(repo_path),
            github_owner=github_owner,
            github_repo=github_repo,
            original_request=request,
        )

        ensure_workspace(repo_path)

        state.mark_completed("inspect_repository")
        state.mark_completed("initialize_workspace")

        if github_owner and github_repo:
            feature_request = run_intake_agent(
                raw_request=request,
                repo_path=str(repo_path),
            )
            issue_spec = run_product_owner_agent(feature_request)

            state.feature_request_title = feature_request.title
            state.feature_request_summary = feature_request.summary
            state.issue_spec_title = issue_spec.title
            state.issue_spec_labels = issue_spec.labels

            issue = create_github_issue(
                owner=github_owner,
                repo=github_repo,
                title=issue_spec.title,
                body=issue_spec.body,
                labels=issue_spec.labels,
            )

            state.github_issue_number = issue.number
            state.github_issue_url = issue.url
            state.mark_completed("analyze_feature_request")
            state.mark_completed("create_github_issue")

            branch_name = build_feature_branch_name(
                issue_number=issue.number,
                request=request,
            )

            create_branch(repo_path, branch_name)
            state.branch_name = branch_name
            state.mark_completed("create_feature_branch")

            architecture_review = build_architecture_review(repo_path, request)
            implementation_plan = build_implementation_plan(architecture_review)

            state.architecture_review_summary = architecture_review.summary
            state.detected_stack = architecture_review.detected_stack
            state.affected_areas = architecture_review.affected_areas
            state.likely_files = architecture_review.likely_files
            state.risk_notes = architecture_review.risks
            state.security_notes = architecture_review.security_notes
            state.testing_notes = architecture_review.testing_notes
            state.devops_notes = architecture_review.devops_notes
            state.implementation_plan = implementation_plan.steps

            state.mark_completed("run_architecture_review")
            state.mark_completed("generate_implementation_plan")

            patch_proposal = build_patch_proposal(
                request=request,
                likely_files=state.likely_files,
                implementation_plan=state.implementation_plan,
            )

            state.patch_summary = patch_proposal.summary
            state.patch_affected_files = patch_proposal.affected_files
            state.proposed_changes = patch_proposal.proposed_changes
            state.patch_risk_level = patch_proposal.risk_level

            approval_request = build_approval_request(repo_path, state, "apply_patch")
            apply_approval_request_to_state(state, approval_request)

            state.mark_completed("prepare_patch")
            state.mark_completed("request_patch_approval")
        else:
            state.last_error = (
                "GitHub owner/repo was not provided. "
                "Skipping GitHub issue and branch creation."
            )

        save_state(state)
        update_delivery_markdown(state)
        if state.implementation_plan:
            console.print("[green]Architecture review and implementation plan generated.[/green]")

        if state.pending_approval and state.pending_action:
            console.print(
                f"[yellow]Waiting for approval:[/yellow] {state.pending_action}"
            )

        console.print("[green]DeliveryOps run initialized.[/green]")
        console.print(f"Request ID: {request_id}")
        console.print(f"Current Step: {state.current_step}")

        if state.github_issue_url:
            console.print(f"GitHub Issue: {state.github_issue_url}")
        else:
            console.print("[yellow]GitHub issue was not created.[/yellow]")

        if state.branch_name:
            console.print(f"Branch: {state.branch_name}")

        console.print(f"Tracking file: {repo_path / '.deliveryops' / 'DELIVERY.md'}")
