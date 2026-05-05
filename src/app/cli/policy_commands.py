import typer

from app.cli.common import console, resolve_repo_path
from app.state_store import load_state, save_state
from app.tools.markdown_tracking_tools import update_delivery_markdown
from app.tools.policy_profile_tools import evaluate_policy_action, validate_policy_profile


def register_policy_commands(app: typer.Typer) -> None:
    @app.command("set-policy-profile")
    def set_policy_profile_command(
        repo: str = typer.Option(".", help="Path to the local repository."),
        profile: str = typer.Option(..., help="Policy profile: sandbox, personal_repo, production_repo."),
    ):
        repo_path = resolve_repo_path(repo)
        state = load_state(repo_path)

        selected_profile = validate_policy_profile(profile)

        state.policy_profile = selected_profile
        state.mark_completed("set_policy_profile")

        save_state(state)
        update_delivery_markdown(state)

        console.print("[green]Policy profile updated.[/green]")
        console.print(f"Profile: {selected_profile}")

    @app.command("policy-status")
    def policy_status_command(
        repo: str = typer.Option(".", help="Path to the local repository."),
        action: str | None = typer.Option(None, help="Optional action to evaluate."),
    ):
        repo_path = resolve_repo_path(repo)
        state = load_state(repo_path)

        console.print("[bold]DeliveryOps Policy Status[/bold]")
        console.print(f"Active Profile: {state.policy_profile}")

        if action:
            decision = evaluate_policy_action(state, action)

            console.print("")
            console.print(f"Action: {decision.action}")
            console.print(f"Permission: {decision.permission}")
            console.print(f"Reason: {decision.reason}")

            if decision.blockers:
                console.print("")
                console.print("[red]Blockers[/red]")
                for blocker in decision.blockers:
                    console.print(f"- {blocker}")

            if decision.warnings:
                console.print("")
                console.print("[yellow]Warnings[/yellow]")
                for warning in decision.warnings:
                    console.print(f"- {warning}")
