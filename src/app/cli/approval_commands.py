import typer

from app.cli.common import console, resolve_repo_path
from app.schemas.approval_record import ApprovalRecord
from app.state_store import load_state, save_state
from app.tools.approval_request_tools import (
    apply_approval_request_to_state,
    build_approval_request,
)
from app.tools.approval_tools import append_approval_record
from app.tools.markdown_tracking_tools import update_delivery_markdown


def register_approval_commands(app: typer.Typer) -> None:
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
            risk_level=state.approval_request_risk_level,
            affected_files=state.approval_request_affected_files,
            command=state.approval_request_command,
            expected_result=state.approval_request_expected_result,
            rollback_note=state.approval_request_rollback_note,
            policy_profile=state.policy_profile,
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
            risk_level=state.approval_request_risk_level,
            affected_files=state.approval_request_affected_files,
            command=state.approval_request_command,
            expected_result=state.approval_request_expected_result,
            rollback_note=state.approval_request_rollback_note,
            policy_profile=state.policy_profile,
        )

        append_approval_record(repo_path, record)

        state.pending_approval = False
        state.pending_action = None
        state.last_error = f"User rejected action: {action}"

        save_state(state)
        update_delivery_markdown(state)

        console.print(f"[yellow]Rejected action:[/yellow] {action}")
        console.print(f"Approval history: {repo_path / '.deliveryops' / 'approvals.md'}")

    @app.command("approval-status")
    def approval_status_command(
        repo: str = typer.Option(".", help="Path to the local repository."),
    ):
        repo_path = resolve_repo_path(repo)
        state = load_state(repo_path)

        if not state.pending_approval and not state.pending_action:
            console.print("[green]No pending approval.[/green]")
            raise typer.Exit(code=0)

        action = state.pending_action or state.approval_request_action

        if action and not state.approval_request_action:
            request = build_approval_request(repo_path, state, action)
            apply_approval_request_to_state(state, request)
            save_state(state)
            update_delivery_markdown(state)

        console.print("[bold]Pending Approval Request[/bold]")
        console.print(f"Action: {state.approval_request_action or state.pending_action}")
        console.print(f"Risk Level: {state.approval_request_risk_level or 'pending'}")
        console.print(f"Reason: {state.approval_request_reason or 'pending'}")

        if state.approval_request_command:
            console.print("")
            console.print("[bold]Command[/bold]")
            console.print(state.approval_request_command)

        if state.approval_request_affected_files:
            console.print("")
            console.print("[bold]Affected Files[/bold]")
            for file_path in state.approval_request_affected_files:
                console.print(f"- {file_path}")

        if state.approval_request_expected_result:
            console.print("")
            console.print("[bold]Expected Result[/bold]")
            console.print(state.approval_request_expected_result)

        if state.approval_request_rollback_note:
            console.print("")
            console.print("[bold]Rollback Note[/bold]")
            console.print(state.approval_request_rollback_note)
