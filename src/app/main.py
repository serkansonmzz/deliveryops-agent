import uuid
from pathlib import Path
import typer
from rich.console import Console

from app.config import resolve_repo_path
from app.schemas.delivery_state import DeliveryState
from app.state_store import ensure_workspace, save_state, load_state
from app.tools.branch_name_tools import build_feature_branch_name
from app.tools.git_tools import (
    ensure_git_repo,
    get_current_branch,
    get_git_status,
    create_branch,
)
from app.tools.github_tools import (
    ensure_gh_authenticated,
    create_github_issue,
)
from app.tools.architecture_review_tools import (
    build_architecture_review,
    build_implementation_plan,
)
from app.tools.commit_tools import (
    get_commit_candidate_files,
    create_git_commit,
)
from app.tools.pull_request_tools import (
    create_draft_pull_request,
    build_pull_request_body,
    build_pull_request_title,
)
from app.tools.push_tools import push_current_branch
from app.tools.commit_message_tools import build_commit_message_spec
from app.tools.agent_patch_tools import generate_patch_with_agent
from app.tools.patch_generator_tools import generate_patch
from app.tools.apply_patch_tools import apply_available_patch
from app.tools.approval_tools import append_approval_record, has_approved_action
from app.schemas.approval_record import ApprovalRecord
from app.tools.patch_proposal_tools import build_patch_proposal
from app.tools.issue_body_tools import build_issue_spec
from app.tools.markdown_tracking_tools import update_delivery_markdown


app = typer.Typer(help="DeliveryOps Agent CLI")
console = Console()


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


@app.command()
def approve(
    repo: str = typer.Option(".", help="Path to the local repository."),
    action: str = typer.Option(..., help="Action to approve."),
    reason: str | None = typer.Option(None, help="Optional approval reason."),
):
    repo_path = resolve_repo_path(repo)
    state = load_state(repo_path)

    if not state.pending_approval:
        console.print("[yellow]No approval is currently pending.[/yellow]")
        raise typer.Exit(code=0)

    if state.pending_action != action:
        console.print(
            f"[red]Pending action mismatch.[/red] "
            f"Expected `{state.pending_action}`, got `{action}`."
        )
        raise typer.Exit(code=1)

    record = ApprovalRecord(
        request_id=state.request_id,
        action=action,
        decision="approved",
        reason=reason,
    )

    append_approval_record(repo_path, record)

    state.pending_approval = False
    state.pending_action = None
    state.last_error = None

    save_state(state)
    update_delivery_markdown(state)

    console.print(f"[green]Approved action:[/green] {action}")
    console.print(f"Approval history: {repo_path / '.deliveryops' / 'approvals.md'}")


@app.command()
def reject(
    repo: str = typer.Option(".", help="Path to the local repository."),
    action: str = typer.Option(..., help="Action to reject."),
    reason: str | None = typer.Option(None, help="Optional rejection reason."),
):
    repo_path = resolve_repo_path(repo)
    state = load_state(repo_path)

    if not state.pending_approval:
        console.print("[yellow]No approval is currently pending.[/yellow]")
        raise typer.Exit(code=0)

    if state.pending_action != action:
        console.print(
            f"[red]Pending action mismatch.[/red] "
            f"Expected `{state.pending_action}`, got `{action}`."
        )
        raise typer.Exit(code=1)

    record = ApprovalRecord(
        request_id=state.request_id,
        action=action,
        decision="rejected",
        reason=reason,
    )

    append_approval_record(repo_path, record)

    state.pending_approval = False
    state.pending_action = None
    state.last_error = f"User rejected action: {action}"

    save_state(state)
    update_delivery_markdown(state)

    console.print(f"[yellow]Rejected action:[/yellow] {action}")
    console.print(f"Approval history: {repo_path / '.deliveryops' / 'approvals.md'}")

@app.command("generate-patch")
def generate_patch_command(
    repo: str = typer.Option(".", help="Path to the local repository."),
):
    repo_path = resolve_repo_path(repo)
    state = load_state(repo_path)

    patch_path = generate_patch(repo_path, state)

    if patch_path is None:
        state.last_error = (
            "No deterministic patch generator is available for this request yet."
        )
        save_state(state)
        update_delivery_markdown(state)

        console.print(
            "[yellow]No patch generated.[/yellow] "
            "This request is not supported by the deterministic patch generator yet."
        )
        raise typer.Exit(code=0)

    state.mark_completed("prepare_patch")
    state.patch_summary = (
        "A deterministic unified diff patch was generated and saved to "
        ".deliveryops/generated.patch."
    )

    if "README.md" not in state.patch_affected_files:
        state.patch_affected_files.append("README.md")

    if "Generated a README documentation update patch." not in state.proposed_changes:
        state.proposed_changes.append("Generated a README documentation update patch.")

    save_state(state)
    update_delivery_markdown(state)

    console.print("[green]Patch generated.[/green]")
    console.print(f"Patch file: {patch_path.relative_to(repo_path)}")

@app.command("dev-generate-patch")
def dev_generate_patch_command(
    repo: str = typer.Option(".", help="Path to the local repository."),
):
    repo_path = resolve_repo_path(repo)
    state = load_state(repo_path)

    patch_path = generate_patch_with_agent(repo_path, state)

    if patch_path is None:
        state.last_error = "Dev Agent could not generate a patch from the available context."
        save_state(state)
        update_delivery_markdown(state)

        console.print(
            "[yellow]No patch generated.[/yellow] "
            "The Dev Agent could not produce a usable patch."
        )
        raise typer.Exit(code=0)

    state.mark_completed("prepare_patch")
    state.patch_summary = (
        "An Agno Dev Agent generated a unified diff patch and saved it to "
        ".deliveryops/generated.patch."
    )

    if ".deliveryops/generated.patch" not in state.changed_files:
        state.changed_files.append(".deliveryops/generated.patch")

    save_state(state)
    update_delivery_markdown(state)

    console.print("[green]Agent patch generated.[/green]")
    console.print(f"Patch file: {patch_path.relative_to(repo_path)}")

@app.command("apply-patch")
def apply_patch(
    repo: str = typer.Option(".", help="Path to the local repository."),
):
    repo_path = resolve_repo_path(repo)
    state = load_state(repo_path)

    if not has_approved_action(repo_path, state.request_id, "apply_patch"):
        console.print(
            "[red]Cannot apply patch.[/red] "
            "The `apply_patch` action has not been approved."
        )
        raise typer.Exit(code=1)

    result = apply_available_patch(repo_path, state)

    if isinstance(result, Path):
        relative_output_path = result.relative_to(repo_path)

        if str(relative_output_path) not in state.changed_files:
            state.changed_files.append(str(relative_output_path))

        console.print("[green]Patch note created.[/green]")
        console.print(f"Created: {relative_output_path}")
    else:
        for changed_file in result.changed_files:
            if changed_file not in state.changed_files:
                state.changed_files.append(changed_file)

        console.print("[green]Unified diff patch applied.[/green]")
        console.print(f"Patch file: {result.patch_path}")

    state.pending_action = None
    state.pending_approval = False
    state.mark_completed("apply_patch")

    save_state(state)
    update_delivery_markdown(state)

    console.print("[green]Apply patch workflow completed.[/green]")

@app.command("generate-commit-message")
def generate_commit_message_command(
    repo: str = typer.Option(".", help="Path to the local repository."),
):
    repo_path = resolve_repo_path(repo)
    state = load_state(repo_path)

    commit_spec = build_commit_message_spec(repo_path, state)

    if not commit_spec.changed_files:
        state.last_error = "No changed files detected. Commit message was not generated."
        save_state(state)
        update_delivery_markdown(state)

        console.print("[yellow]No changed files detected.[/yellow]")
        raise typer.Exit(code=0)

    state.commit_message = commit_spec.subject
    state.commit_body = commit_spec.body
    state.commit_diff_summary = commit_spec.diff_summary
    state.commit_rationale = commit_spec.rationale
    state.changed_files = commit_spec.changed_files

    state.pending_action = "git_commit"
    state.pending_approval = True

    state.mark_completed("generate_commit_message")
    state.mark_completed("request_commit_approval")

    save_state(state)
    update_delivery_markdown(state)

    console.print("[green]Commit message generated.[/green]")
    console.print(f"Subject: {commit_spec.subject}")
    console.print("[yellow]Waiting for approval:[/yellow] git_commit")

@app.command("commit")
def commit_command(
    repo: str = typer.Option(".", help="Path to the local repository."),
):
    repo_path = resolve_repo_path(repo)
    state = load_state(repo_path)

    if not has_approved_action(repo_path, state.request_id, "git_commit"):
        console.print(
            "[red]Cannot commit changes.[/red] "
            "The `git_commit` action has not been approved."
        )
        raise typer.Exit(code=1)

    if not state.commit_message:
        console.print(
            "[red]Cannot commit changes.[/red] "
            "No commit message has been generated yet."
        )
        raise typer.Exit(code=1)

    candidate_files = get_commit_candidate_files(repo_path)

    if not candidate_files:
        state.last_error = "No commit-safe changed files detected."
        save_state(state)
        update_delivery_markdown(state)

        console.print("[yellow]No commit-safe changed files detected.[/yellow]")
        raise typer.Exit(code=0)

    result = create_git_commit(
        repo_path=repo_path,
        subject=state.commit_message,
        body=state.commit_body,
        files=candidate_files,
    )

    state.commit_hash = result.commit_hash
    state.committed_files = result.committed_files
    state.changed_files = result.committed_files

    state.pending_action = "git_push"
    state.pending_approval = True

    state.mark_completed("commit_changes")
    state.mark_completed("request_push_approval")

    save_state(state)
    update_delivery_markdown(state)

    console.print("[green]Git commit created.[/green]")
    console.print("[yellow]Waiting for approval:[/yellow] git_push")
    console.print(f"Commit: {result.commit_hash}")
    console.print(f"Subject: {result.subject}")

@app.command("push")
def push_command(
    repo: str = typer.Option(".", help="Path to the local repository."),
    remote: str = typer.Option("origin", help="Git remote name."),
):
    repo_path = resolve_repo_path(repo)
    state = load_state(repo_path)

    if not has_approved_action(repo_path, state.request_id, "git_push"):
        console.print(
            "[red]Cannot push branch.[/red] "
            "The `git_push` action has not been approved."
        )
        raise typer.Exit(code=1)

    result = push_current_branch(repo_path, remote=remote)

    state.push_remote = result.remote
    state.pushed_branch = result.branch_name
    state.push_status = "pushed"
    state.push_output = result.stdout or result.stderr or "Push completed."

    state.pending_action = "create_draft_pull_request"
    state.pending_approval = True

    state.mark_completed("push_branch")
    state.mark_completed("request_pr_approval")

    save_state(state)
    update_delivery_markdown(state)

    console.print("[yellow]Waiting for approval:[/yellow] create_draft_pull_request")
    console.print("[green]Branch pushed.[/green]")
    console.print(f"Remote: {result.remote}")
    console.print(f"Branch: {result.branch_name}")

@app.command("open-draft-pr")
def open_draft_pr_command(
    repo: str = typer.Option(".", help="Path to the local repository."),
    base_branch: str = typer.Option("main", help="Base branch for the pull request."),
):
    repo_path = resolve_repo_path(repo)
    state = load_state(repo_path)

    if not has_approved_action(repo_path, state.request_id, "create_draft_pull_request"):
        console.print(
            "[red]Cannot open draft PR.[/red] "
            "The `create_draft_pull_request` action has not been approved."
        )
        raise typer.Exit(code=1)

    pr_body = build_pull_request_body(state)
    pr_title = build_pull_request_title(state)

    result = create_draft_pull_request(
        repo_path=repo_path,
        state=state,
        base_branch=base_branch,
    )

    state.pr_url = result.url
    state.pr_title = pr_title
    state.pr_body = pr_body
    state.pr_base_branch = result.base_branch
    state.pr_head_branch = result.head_branch
    state.pr_status = "draft_opened"

    state.pending_action = None
    state.pending_approval = False

    state.mark_completed("open_draft_pr")

    save_state(state)
    update_delivery_markdown(state)

    console.print("[green]Draft pull request opened.[/green]")
    console.print(f"PR: {result.url}")

@app.command("github-check")
def github_check():
    ensure_gh_authenticated()
    console.print("[green]GitHub CLI is available and authenticated.[/green]")


@app.command("create-issue")
def create_issue(
    github_owner: str = typer.Option(..., help="GitHub owner/user/org."),
    github_repo: str = typer.Option(..., help="GitHub repository name."),
    title: str = typer.Option(..., help="Issue title."),
    body: str = typer.Option(..., help="Issue body."),
):
    issue = create_github_issue(
        owner=github_owner,
        repo=github_repo,
        title=title,
        body=body,
    )

    console.print("[green]GitHub issue created.[/green]")
    console.print(f"Issue #{issue.number}: {issue.url}")


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


@app.command()
def run(
    repo: str = typer.Option(".", help="Path to the local repository."),
    github_owner: str | None = typer.Option(None, help="GitHub owner/user/org."),
    github_repo: str | None = typer.Option(None, help="GitHub repository name."),
    request: str = typer.Option(..., help="Feature request text."),
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
        issue_spec = build_issue_spec(request)

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

        state.pending_action = "apply_patch"
        state.pending_approval = True

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


if __name__ == "__main__":
    app()