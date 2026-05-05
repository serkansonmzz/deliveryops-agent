import typer

from app.cli.common import console, resolve_repo_path
from app.services.test_service import (
    analyze_failed_tests,
    detect_tests,
    run_tests,
)


def register_test_commands(app: typer.Typer) -> None:
    @app.command("detect-tests")
    def detect_tests_command(
        repo: str = typer.Option(".", help="Path to the local repository."),
    ):
        repo_path = resolve_repo_path(repo)
        result = detect_tests(repo_path)

        if result.status == "detected":
            console.print("[green]Test command detected.[/green]")
            console.print(f"Command: {result.details.get('command')}")
            return

        console.print("[yellow]No test command detected.[/yellow]")

    @app.command("run-tests")
    def run_tests_command(
        repo: str = typer.Option(".", help="Path to the local repository."),
    ):
        repo_path = resolve_repo_path(repo)
        result = run_tests(repo_path)

        if result.status == "passed":
            console.print("[green]Tests passed.[/green]")
        elif result.status == "failed":
            console.print("[red]Tests failed.[/red]")
        else:
            console.print("[yellow]No test command detected.[/yellow]")

        if "command" in result.details:
            console.print(f"Command: {result.details.get('command')}")

        if "exit_code" in result.details:
            console.print(f"Exit Code: {result.details.get('exit_code')}")

        if result.exit_code != 0:
            raise typer.Exit(code=result.exit_code)

    @app.command("analyze-test-failure")
    def analyze_test_failure_command(
        repo: str = typer.Option(".", help="Path to the local repository."),
    ):
        repo_path = resolve_repo_path(repo)
        result = analyze_failed_tests(repo_path)

        if result.status == "skipped":
            console.print("[yellow]No failed test run found.[/yellow]")
            return

        console.print("[green]Test failure analyzed.[/green]")
        console.print(f"Category: {result.details.get('category')}")
        console.print(f"Risk Level: {result.details.get('risk_level')}")
