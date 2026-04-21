import uuid
from pathlib import Path
import typer
from rich.console import Console
from app.tools.issue_body_tools import build_issue_spec
from app.config import resolve_repo_path
from app.schemas.delivery_state import DeliveryState
from app.state_store import ensure_workspace, save_state, load_state
from app.tools.git_tools import ensure_git_repo, get_current_branch, get_git_status
from app.tools.markdown_tracking_tools import update_delivery_markdown
from app.tools.github_tools import (
    ensure_gh_authenticated,
    create_github_issue,
)

app = typer.Typer(help="DeliveryOps Agent CLI")
console = Console()


@app.command()
def init(
    repo: str = typer.Option(".", help="Path to the local repository."),
    request: str = typer.Option("Initial DeliveryOps workspace setup.", help="Initial request text."),
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

    console.print(f"[green]DeliveryOps workspace initialized.[/green]")
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

@app.command("github-check")
def github_check():
    ensure_gh_authenticated()
    console.print("[green]GitHub CLI is available and authenticated.[/green]")


@app.command("create-issue")
def create_issue(
    github_owner: str = typer.Option(..., help="GitHub owner/user/org."),
    github_repo: str = typer.Option(..., help="GitHub repository name."),
    title: str = typer.Option(..., help="Issue title."),
    body: str = typer.Option(..., help="Issue body."),):
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
    else:
        state.last_error = (
            "GitHub owner/repo was not provided. Skipping GitHub issue creation."
        )

    save_state(state)
    update_delivery_markdown(state)

    console.print("[green]DeliveryOps run initialized.[/green]")
    console.print(f"Request ID: {request_id}")
    console.print(f"Current Step: {state.current_step}")

    if state.github_issue_url:
        console.print(f"GitHub Issue: {state.github_issue_url}")
    else:
        console.print("[yellow]GitHub issue was not created.[/yellow]")

    console.print(f"Tracking file: {repo_path / '.deliveryops' / 'DELIVERY.md'}")


if __name__ == "__main__":
    app()