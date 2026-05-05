import typer

from app.cli.common import console, resolve_repo_path
from app.state_store import load_state, save_state
from app.tools.approval_tools import has_approved_action
from app.tools.ci_tools import apply_ci_status_to_state, check_pull_request_ci_status
from app.tools.github_tools import create_github_issue, ensure_gh_authenticated
from app.tools.issue_comment_tools import post_progress_comment
from app.tools.markdown_tracking_tools import update_delivery_markdown
from app.tools.policy_profile_tools import ensure_policy_allows_action
from app.tools.pull_request_tools import (
    build_pull_request_body,
    build_pull_request_title,
    create_draft_pull_request,
)


def register_github_commands(app: typer.Typer) -> None:
    @app.command("github-check")
    def github_check():
        ensure_gh_authenticated()
        console.print("[green]GitHub CLI is available and authenticated.[/green]")

    @app.command("comment-progress")
    def comment_progress_command(
        repo: str = typer.Option(".", help="Path to the local repository."),
    ):
        repo_path = resolve_repo_path(repo)
        state = load_state(repo_path)

        ensure_policy_allows_action(state, "comment_progress")

        comment_output = post_progress_comment(repo_path, state)

        state.issue_comment_count += 1
        state.last_issue_comment_url = comment_output.strip() or None

        state.mark_completed("comment_progress")

        save_state(state)
        update_delivery_markdown(state)

        console.print("[green]Progress comment posted.[/green]")

        if state.last_issue_comment_url:
            console.print(f"Comment: {state.last_issue_comment_url}")

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

    @app.command("open-draft-pr")
    def open_draft_pr_command(
        repo: str = typer.Option(".", help="Path to the local repository."),
        base_branch: str = typer.Option("main", help="Base branch for the pull request."),
    ):
        repo_path = resolve_repo_path(repo)
        state = load_state(repo_path)

        ensure_policy_allows_action(state, "create_draft_pull_request")

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

    @app.command("check-ci")
    def check_ci_command(
        repo: str = typer.Option(".", help="Path to the local repository."),
    ):
        repo_path = resolve_repo_path(repo)
        state = load_state(repo_path)

        result = check_pull_request_ci_status(repo_path, state)
        apply_ci_status_to_state(state, result)

        save_state(state)
        update_delivery_markdown(state)

        console.print("[bold]GitHub CI Status[/bold]")
        console.print(f"Status: {result.status}")
        console.print(result.summary)

        if result.status == "failed":
            console.print("")
            console.print("[red]Failed Checks[/red]")
            for check in state.ci_failed_checks:
                console.print(f"- {check}")

            raise typer.Exit(code=1)

        if result.status == "pending":
            console.print("")
            console.print("[yellow]Pending Checks[/yellow]")
            for check in state.ci_pending_checks:
                console.print(f"- {check}")
