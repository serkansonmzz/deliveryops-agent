import typer

from app.cli.common import console, resolve_repo_path
from app.state_store import load_state, save_state
from app.tools.markdown_tracking_tools import update_delivery_markdown
from app.tools.test_failure_analysis_tools import analyze_test_failure
from app.tools.test_tools import detect_test_command, run_safe_test_command


def register_test_commands(app: typer.Typer) -> None:
    @app.command("detect-tests")
    def detect_tests_command(
        repo: str = typer.Option(".", help="Path to the local repository."),
    ):
        repo_path = resolve_repo_path(repo)
        state = load_state(repo_path)

        command = detect_test_command(repo_path)

        if command is None:
            state.test_status = "not_detected"
            state.test_command = None
            state.test_summary = "No known test command was detected."
            state.mark_completed("detect_tests")

            save_state(state)
            update_delivery_markdown(state)

            console.print("[yellow]No test command detected.[/yellow]")
            raise typer.Exit(code=0)

        state.test_command = command
        state.test_status = "detected"
        state.test_summary = f"Detected test command: {command}"
        state.mark_completed("detect_tests")

        save_state(state)
        update_delivery_markdown(state)

        console.print("[green]Test command detected.[/green]")
        console.print(f"Command: {command}")

    @app.command("run-tests")
    def run_tests_command(
        repo: str = typer.Option(".", help="Path to the local repository."),
    ):
        repo_path = resolve_repo_path(repo)
        state = load_state(repo_path)

        if not state.test_command:
            detected = detect_test_command(repo_path)

            if not detected:
                state.test_status = "not_detected"
                state.test_summary = "No known test command was detected."
                state.mark_completed("detect_tests")

                save_state(state)
                update_delivery_markdown(state)

                console.print("[yellow]No test command detected.[/yellow]")
                raise typer.Exit(code=0)

            state.test_command = detected
            state.mark_completed("detect_tests")

        result = run_safe_test_command(repo_path, state.test_command)

        state.test_status = result.status
        state.test_exit_code = result.exit_code
        state.test_output = "\n".join(
            part for part in [result.stdout, result.stderr] if part.strip()
        )
        state.test_summary = result.summary
        state.mark_completed("run_tests")

        save_state(state)
        update_delivery_markdown(state)

        if result.status == "passed":
            console.print("[green]Tests passed.[/green]")
        else:
            console.print("[red]Tests failed.[/red]")

        console.print(f"Command: {result.command}")
        console.print(f"Exit Code: {result.exit_code}")

        if result.status != "passed":
            raise typer.Exit(code=1)

    @app.command("analyze-test-failure")
    def analyze_test_failure_command(
        repo: str = typer.Option(".", help="Path to the local repository."),
    ):
        repo_path = resolve_repo_path(repo)
        state = load_state(repo_path)

        if state.test_status != "failed":
            console.print("[yellow]No failed test run found.[/yellow]")
            raise typer.Exit(code=0)

        analysis = analyze_test_failure(state)

        state.test_failure_category = analysis.category
        state.test_failure_analysis_summary = analysis.summary
        state.test_failure_likely_causes = analysis.likely_causes
        state.test_failure_next_actions = analysis.next_actions
        state.test_failure_risk_level = analysis.risk_level

        state.mark_completed("analyze_test_failure")

        save_state(state)
        update_delivery_markdown(state)

        console.print("[green]Test failure analyzed.[/green]")
        console.print(f"Category: {analysis.category}")
        console.print(f"Risk Level: {analysis.risk_level}")
