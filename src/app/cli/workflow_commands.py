import uuid

import typer

from app.cli.common import console, resolve_repo_path
from app.cli.heartbeat import run_with_heartbeat
from app.schemas.delivery_state import DeliveryState
from app.services.agent_intake_service import run_intake_agent
from app.services.architecture_council_service import (
    build_architecture_review_for_state,
    run_architecture_council_agent,
)
from app.services.implementation_plan_service import (
    build_implementation_plan_for_state,
    run_implementation_planner_agent,
)
from app.services.issue_spec_service import run_product_owner_agent
from app.services.repo_analysis_service import run_repo_analysis
from app.services.workflow_service import get_workflow_status, run_auto_continue
from app.state_store import ensure_workspace, load_state, save_state
from app.tools.approval_request_tools import (
    apply_approval_request_to_state,
    build_approval_request,
)
from app.tools.architecture_review_tools import (
    apply_architecture_review_to_state,
)
from app.tools.branch_name_tools import build_feature_branch_name
from app.tools.git_tools import (
    create_branch,
    ensure_git_repo,
    get_current_branch,
    get_git_status,
)
from app.tools.github_tools import create_github_issue
from app.tools.implementation_plan_tools import apply_implementation_plan_to_state
from app.tools.markdown_tracking_tools import update_delivery_markdown
from app.tools.patch_proposal_tools import build_patch_proposal
from app.tools.repo_analysis_tools import analyze_repository
from app.tools.smoke_test_tools import run_local_smoke_test


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
        result = get_workflow_status(repo_path)

        console.print("[bold]DeliveryOps Workflow Status[/bold]")
        console.print(f"Status: {result.status}")
        console.print(f"Current Step: {result.details.get('current_step')}")
        console.print(f"Next Action: {result.details.get('next_action') or 'none'}")
        console.print(f"Safe To Run: {result.details.get('safe_to_run')}")
        console.print(f"Requires Approval: {result.details.get('requires_approval')}")
        console.print("")
        console.print(result.message)

        if result.details.get("next_command"):
            console.print("")
            console.print("[bold]Next Command[/bold]")
            console.print(str(result.details.get("next_command")))

        if result.errors:
            console.print("")
            console.print("[red]Blockers[/red]")
            for error in result.errors:
                console.print(f"- {error}")

        if result.warnings:
            console.print("")
            console.print("[yellow]Notes[/yellow]")
            for note in result.warnings:
                console.print(f"- {note}")

    @app.command("auto-continue")
    def auto_continue_command(
        repo: str = typer.Option(".", help="Path to the local repository."),
        max_steps: int = typer.Option(5, help="Maximum number of safe workflow steps to execute."),
    ):
        repo_path = resolve_repo_path(repo)
        result = run_auto_continue(repo_path, max_steps=max_steps)

        console.print("[bold]DeliveryOps Auto-Continue[/bold]")
        console.print(f"Status: {result.status}")
        console.print(result.message)
        console.print(f"Executed Steps: {result.details.get('executed_count', 0)}")

        if result.details.get("next_action"):
            console.print("")
            console.print("[bold]Next Action[/bold]")
            console.print(str(result.details.get("next_action")))

        if result.details.get("next_command"):
            console.print("")
            console.print("[bold]Next Command[/bold]")
            console.print(str(result.details.get("next_command")))

        if result.warnings:
            console.print("")
            console.print("[yellow]Notes[/yellow]")
            for warning in result.warnings:
                console.print(f"- {warning}")

        if result.errors:
            console.print("")
            console.print("[red]Blockers[/red]")
            for error in result.errors:
                console.print(f"- {error}")
            raise typer.Exit(code=1)

        if result.status == "blocked":
            raise typer.Exit(code=1)

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

    @app.command("analyze-repo")
    def analyze_repo_command(
        repo: str = typer.Option(".", help="Path to the local repository."),
    ):
        repo_path = resolve_repo_path(repo)
        result = run_repo_analysis(repo_path)

        console.print("[green]Repository analysis completed.[/green]")
        console.print(result.message)

        if result.details:
            console.print("")
            console.print("[bold]Counts[/bold]")
            for key, value in result.details.items():
                console.print(f"- {key}: {value}")

        if result.warnings:
            console.print("")
            console.print("[yellow]Warnings[/yellow]")
            for warning in result.warnings:
                console.print(f"- {warning}")

    @app.command("architecture-review")
    def architecture_review_command(
        repo: str = typer.Option(".", help="Path to the local repository."),
        no_llm: bool = typer.Option(
            False,
            "--no-llm",
            help="Use deterministic fallback instead of LLM.",
        ),
    ):
        repo_path = resolve_repo_path(repo)
        result = run_architecture_council_agent(
            repo_path,
            use_llm=False if no_llm else None,
        )

        console.print("[green]Architecture review completed.[/green]")
        console.print(f"Source: {result.details.get('source')}")
        console.print(f"Confidence: {result.details.get('confidence_score')}")
        console.print(result.message)

        if result.warnings:
            console.print("")
            console.print("[yellow]Risks / Warnings[/yellow]")
            for warning in result.warnings:
                console.print(f"- {warning}")

    @app.command("implementation-plan")
    def implementation_plan_command(
        repo: str = typer.Option(".", help="Path to the local repository."),
        no_llm: bool = typer.Option(
            False,
            "--no-llm",
            help="Use deterministic fallback instead of LLM.",
        ),
    ):
        repo_path = resolve_repo_path(repo)
        result = run_implementation_planner_agent(
            repo_path,
            use_llm=False if no_llm else None,
        )

        console.print("[green]Implementation plan generated.[/green]")
        console.print(f"Source: {result.details.get('source')}")
        console.print(f"Confidence: {result.details.get('confidence_score')}")
        console.print(f"Steps: {result.details.get('steps')}")
        console.print(f"Target Files: {result.details.get('target_files')}")
        console.print(result.message)

        if result.warnings:
            console.print("")
            console.print("[yellow]Risks / Warnings[/yellow]")
            for warning in result.warnings:
                console.print(f"- {warning}")

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
        fast: bool = typer.Option(
            False,
            "--fast",
            help="Use deterministic architecture/planning fallbacks for faster setup.",
        ),
        no_llm_planning: bool = typer.Option(
            False,
            "--no-llm-planning",
            help="Use deterministic architecture/planning fallbacks.",
        ),
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
        console.print("[cyan]Workspace initialized.[/cyan]")

        state.mark_completed("inspect_repository")
        state.mark_completed("initialize_workspace")

        console.print("[cyan]Analyzing repository...[/cyan]")
        repo_analysis = analyze_repository(repo_path, request)
        state.detected_stack = repo_analysis.detected_stack
        state.repo_analysis_summary = repo_analysis.summary
        state.repo_source_file_count = len(repo_analysis.source_files)
        state.repo_test_file_count = len(repo_analysis.test_files)
        state.repo_documentation_file_count = len(repo_analysis.documentation_files)
        state.repo_config_file_count = len(repo_analysis.config_files)
        state.repo_risky_files = repo_analysis.risky_files
        state.repo_source_test_map = repo_analysis.source_test_map
        if repo_analysis.likely_files:
            state.likely_files = [item.path for item in repo_analysis.likely_files]
        state.mark_completed("analyze_repository")
        console.print("[green]Repository analysis completed.[/green]")

        if github_owner and github_repo:
            feature_request = run_with_heartbeat(
                "Analyzing feature request with Intake Agent",
                lambda: run_intake_agent(
                    raw_request=request,
                    repo_path=str(repo_path),
                ),
            )
            issue_spec = run_with_heartbeat(
                "Preparing GitHub issue spec with Product Owner Agent",
                lambda: run_product_owner_agent(feature_request),
            )

            state.feature_request_title = feature_request.title
            state.feature_request_summary = feature_request.summary
            state.issue_spec_title = issue_spec.title
            state.issue_spec_labels = issue_spec.labels

            console.print("[cyan]Creating GitHub issue...[/cyan]")
            issue = create_github_issue(
                owner=github_owner,
                repo=github_repo,
                title=issue_spec.title,
                body=issue_spec.body,
                labels=issue_spec.labels,
            )
            if issue.skipped_labels:
                warning = (
                    "Skipped missing GitHub issue labels: "
                    + ", ".join(issue.skipped_labels)
                )
                state.policy_warnings.append(warning)
                console.print(f"[yellow]{warning}[/yellow]")

            state.github_issue_number = issue.number
            state.github_issue_url = issue.url
            state.mark_completed("analyze_feature_request")
            state.mark_completed("create_github_issue")
            console.print(f"[green]GitHub issue created:[/green] {issue.url}")

            branch_name = build_feature_branch_name(
                issue_number=issue.number,
                request=request,
            )

            console.print(f"[cyan]Creating feature branch:[/cyan] {branch_name}")
            create_branch(repo_path, branch_name)
            state.branch_name = branch_name
            state.mark_completed("create_feature_branch")
            console.print("[green]Feature branch created.[/green]")

            architecture_review = run_with_heartbeat(
                "Running architecture review with Architecture Council Agent",
                lambda: build_architecture_review_for_state(
                    state,
                    use_llm=False if fast or no_llm_planning else None,
                ),
            )
            apply_architecture_review_to_state(state, architecture_review)
            console.print("[green]Architecture review completed.[/green]")

            implementation_plan = run_with_heartbeat(
                "Generating implementation plan with Planner Agent",
                lambda: build_implementation_plan_for_state(
                    state,
                    use_llm=False if fast or no_llm_planning else None,
                ),
            )
            apply_implementation_plan_to_state(state, implementation_plan)
            console.print("[green]Implementation plan generated.[/green]")

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
            console.print("[green]Patch approval request prepared.[/green]")
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
