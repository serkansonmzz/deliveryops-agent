import typer

from app.cli.common import console, resolve_repo_path
from app.state_store import load_state, save_state
from app.tools.delivery_report_tools import build_final_report, write_final_report
from app.tools.markdown_tracking_tools import update_delivery_markdown
from app.tools.release_candidate_tools import (
    apply_mvp_release_candidate_state,
    write_mvp_release_notes,
)
from app.tools.release_judge_tools import (
    apply_readiness_result_to_state,
    evaluate_release_readiness,
)


def register_release_commands(app: typer.Typer) -> None:
    @app.command("readiness-check")
    def readiness_check_command(
        repo: str = typer.Option(".", help="Path to the local repository."),
    ):
        repo_path = resolve_repo_path(repo)
        state = load_state(repo_path)

        result = evaluate_release_readiness(repo_path, state)
        apply_readiness_result_to_state(state, result)

        save_state(state)
        update_delivery_markdown(state)

        console.print("[bold]Release Readiness Check[/bold]")
        console.print(f"Status: {result.status}")
        console.print(f"Risk Level: {result.risk_level}")
        console.print(result.summary)

        if result.blockers:
            console.print("")
            console.print("[red]Blockers[/red]")
            for blocker in result.blockers:
                console.print(f"- {blocker}")

        if result.warnings:
            console.print("")
            console.print("[yellow]Warnings[/yellow]")
            for warning in result.warnings:
                console.print(f"- {warning}")

        if result.next_actions:
            console.print("")
            console.print("[bold]Next Actions[/bold]")
            for action in result.next_actions:
                console.print(f"- {action}")

        if result.status == "blocked":
            raise typer.Exit(code=1)

    @app.command("final-report")
    def final_report_command(
        repo: str = typer.Option(".", help="Path to the local repository."),
    ):
        repo_path = resolve_repo_path(repo)
        state = load_state(repo_path)

        report = build_final_report(state)
        report_path = write_final_report(repo_path, report)

        state.final_report_path = str(report_path.relative_to(repo_path))
        state.final_report_status = "generated"

        state.mark_completed("generate_final_report")

        save_state(state)
        update_delivery_markdown(state)

        console.print("[green]Final report generated.[/green]")
        console.print(f"Report: {state.final_report_path}")

    @app.command("mvp-release-notes")
    def mvp_release_notes_command(
        repo: str = typer.Option(".", help="Path to the local repository."),
    ):
        repo_path = resolve_repo_path(repo)
        state = load_state(repo_path)

        notes_path = write_mvp_release_notes(repo_path, state)
        apply_mvp_release_candidate_state(state, notes_path, repo_path)

        save_state(state)
        update_delivery_markdown(state)

        console.print("[green]MVP release notes generated.[/green]")
        console.print(f"Release notes: {state.mvp_release_notes_path}")
