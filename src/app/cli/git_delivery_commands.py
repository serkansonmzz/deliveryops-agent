import typer

from app.cli.common import console, resolve_repo_path
from app.state_store import load_state, save_state
from app.tools.approval_request_tools import (
    apply_approval_request_to_state,
    build_approval_request,
)
from app.tools.approval_tools import has_approved_action
from app.tools.commit_message_tools import build_commit_message_spec
from app.tools.commit_tools import create_git_commit, get_commit_candidate_files
from app.tools.markdown_tracking_tools import update_delivery_markdown
from app.tools.policy_profile_tools import ensure_policy_allows_action
from app.tools.push_tools import push_current_branch


def register_git_delivery_commands(app: typer.Typer) -> None:
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

        approval_request = build_approval_request(repo_path, state, "git_commit")
        apply_approval_request_to_state(state, approval_request)

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

        ensure_policy_allows_action(state, "git_commit")

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

        approval_request = build_approval_request(repo_path, state, "git_push")
        apply_approval_request_to_state(state, approval_request)

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

        ensure_policy_allows_action(state, "git_push")

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

        approval_request = build_approval_request(repo_path, state, "create_draft_pull_request")
        apply_approval_request_to_state(state, approval_request)

        state.mark_completed("push_branch")
        state.mark_completed("request_pr_approval")

        save_state(state)
        update_delivery_markdown(state)

        console.print("[yellow]Waiting for approval:[/yellow] create_draft_pull_request")
        console.print("[green]Branch pushed.[/green]")
        console.print(f"Remote: {result.remote}")
        console.print(f"Branch: {result.branch_name}")
