import typer

from app.cli.common import console, resolve_repo_path
from app.services.release_service import (
    generate_final_report,
    generate_mvp_release_notes,
    run_readiness_check,
)


def register_release_commands(app: typer.Typer) -> None:
    @app.command("readiness-check")
    def readiness_check_command(
        repo: str = typer.Option(".", help="Path to the local repository."),
    ):
        repo_path = resolve_repo_path(repo)
        result = run_readiness_check(repo_path)

        console.print("[bold]Release Readiness Check[/bold]")
        console.print(f"Status: {result.status}")
        console.print(f"Risk Level: {result.details.get('risk_level')}")
        console.print(result.message)

        if result.errors:
            console.print("")
            console.print("[red]Blockers[/red]")
            for error in result.errors:
                console.print(f"- {error}")

        if result.warnings:
            console.print("")
            console.print("[yellow]Warnings[/yellow]")
            for warning in result.warnings:
                console.print(f"- {warning}")

        if result.exit_code != 0:
            raise typer.Exit(code=result.exit_code)

    @app.command("final-report")
    def final_report_command(
        repo: str = typer.Option(".", help="Path to the local repository."),
    ):
        repo_path = resolve_repo_path(repo)
        result = generate_final_report(repo_path)

        console.print("[green]Final report generated.[/green]")
        console.print(f"Report: {result.details.get('report_path')}")

    @app.command("mvp-release-notes")
    def mvp_release_notes_command(
        repo: str = typer.Option(".", help="Path to the local repository."),
    ):
        repo_path = resolve_repo_path(repo)
        result = generate_mvp_release_notes(repo_path)

        console.print("[green]MVP release notes generated.[/green]")
        console.print(f"Release notes: {result.details.get('release_notes')}")
