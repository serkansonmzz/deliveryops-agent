import typer

from app.cli.common import console, resolve_repo_path
from app.state_store import load_state, save_state
from app.tools.agent_role_tools import list_agent_roles, summarize_agent_role_status
from app.tools.markdown_tracking_tools import update_delivery_markdown


def register_agent_commands(app: typer.Typer) -> None:
    @app.command("agent-roles")
    def agent_roles_command(
        repo: str = typer.Option(".", help="Path to the local repository."),
    ):
        # repo option is accepted for CLI consistency.
        roles = list_agent_roles()

        console.print("[bold]DeliveryOps Agent Roles[/bold]")

        for role in roles:
            console.print("")
            console.print(f"[bold]{role.role_id}[/bold] - {role.display_name}")
            console.print(role.purpose)
            console.print(f"Implemented: {len(role.implemented_capabilities)}")
            console.print(f"Future: {len(role.future_capabilities)}")

    @app.command("agent-role-status")
    def agent_role_status_command(
        repo: str = typer.Option(".", help="Path to the local repository."),
        role: str = typer.Option(..., help="Agent role id, e.g. dev_agent."),
    ):
        repo_path = resolve_repo_path(repo)
        state = load_state(repo_path)

        status = summarize_agent_role_status(role)

        state.last_agent_role_reviewed = status.role_id
        state.agent_role_status_summary = status.summary
        state.agent_role_notes = status.notes

        state.mark_completed("agent_role_status_review")

        save_state(state)
        update_delivery_markdown(state)

        console.print("[bold]Agent Role Status[/bold]")
        console.print(f"Role: {status.display_name}")
        console.print(f"Status: {status.status}")
        console.print(status.summary)

        if status.implemented_capabilities:
            console.print("")
            console.print("[green]Implemented Capabilities[/green]")
            for item in status.implemented_capabilities:
                console.print(f"- {item}")

        if status.future_capabilities:
            console.print("")
            console.print("[yellow]Future Capabilities[/yellow]")
            for item in status.future_capabilities:
                console.print(f"- {item}")

        if status.notes:
            console.print("")
            console.print("[bold]Notes[/bold]")
            for note in status.notes:
                console.print(f"- {note}")
