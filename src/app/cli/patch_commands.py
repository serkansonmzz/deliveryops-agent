from pathlib import Path

import typer

from app.cli.common import console, resolve_repo_path
from app.cli.heartbeat import run_with_heartbeat
from app.state_store import load_state, save_state
from app.tools.agent_patch_tools import MAX_DEV_PATCH_ATTEMPTS, generate_patch_with_agent
from app.tools.apply_patch_tools import apply_available_patch
from app.tools.approval_request_tools import (
    apply_approval_request_to_state,
    build_approval_request,
)
from app.tools.approval_tools import has_approved_action
from app.tools.fix_patch_loop_tools import generate_controlled_fix_patch
from app.tools.markdown_tracking_tools import update_delivery_markdown
from app.tools.patch_generator_tools import generate_patch
from app.tools.policy_profile_tools import ensure_policy_allows_action


def register_patch_commands(app: typer.Typer) -> None:
    @app.command("generate-patch")
    def generate_patch_command(
        repo: str = typer.Option(".", help="Path to the local repository."),
    ):
        repo_path = resolve_repo_path(repo)
        state = load_state(repo_path)

        patch_path = generate_patch(repo_path, state)

        if patch_path is None:
            state.last_error = (
                "No deterministic patch generator is available for this request yet."
            )
            save_state(state)
            update_delivery_markdown(state)

            console.print(
                "[yellow]No patch generated.[/yellow] "
                "This request is not supported by the deterministic patch generator yet."
            )
            raise typer.Exit(code=0)

        state.mark_completed("prepare_patch")
        state.patch_summary = (
            "A deterministic unified diff patch was generated and saved to "
            ".deliveryops/generated.patch."
        )

        if "README.md" not in state.patch_affected_files:
            state.patch_affected_files.append("README.md")

        if "Generated a README documentation update patch." not in state.proposed_changes:
            state.proposed_changes.append("Generated a README documentation update patch.")

        save_state(state)
        update_delivery_markdown(state)

        console.print("[green]Patch generated.[/green]")
        console.print(f"Patch file: {patch_path.relative_to(repo_path)}")

    @app.command("dev-generate-patch")
    def dev_generate_patch_command(
        repo: str = typer.Option(".", help="Path to the local repository."),
    ):
        repo_path = resolve_repo_path(repo)
        state = load_state(repo_path)

        console.print("[cyan]Preparing Dev Agent context...[/cyan]")
        console.print(
            f"[cyan]Working on Dev Agent patch generation "
            f"(up to {MAX_DEV_PATCH_ATTEMPTS} attempts)...[/cyan]"
        )
        try:
            patch_path = run_with_heartbeat(
                "Generating and validating patch with Dev Agent",
                lambda: generate_patch_with_agent(repo_path, state),
            )
        except RuntimeError as exc:
            state = load_state(repo_path)
            state.last_error = str(exc)
            save_state(state)
            update_delivery_markdown(state)
            console.print("[red]Dev Agent patch generation failed.[/red]")
            console.print(str(exc))
            raise typer.Exit(code=1) from exc

        if patch_path is None:
            state.last_error = "Dev Agent could not generate a patch from the available context."
            save_state(state)
            update_delivery_markdown(state)

            console.print(
                "[yellow]No patch generated.[/yellow] "
                "The Dev Agent could not produce a usable patch."
            )
            raise typer.Exit(code=0)

        state.mark_completed("prepare_patch")
        state.patch_summary = (
            "An Agno Dev Agent generated a unified diff patch and saved it to "
            ".deliveryops/generated.patch."
        )

        if ".deliveryops/generated.patch" not in state.changed_files:
            state.changed_files.append(".deliveryops/generated.patch")

        save_state(state)
        update_delivery_markdown(state)

        console.print("[green]Agent patch generated.[/green]")
        console.print(f"Patch file: {patch_path.relative_to(repo_path)}")

    @app.command("apply-patch")
    def apply_patch(
        repo: str = typer.Option(".", help="Path to the local repository."),
    ):
        repo_path = resolve_repo_path(repo)
        state = load_state(repo_path)

        ensure_policy_allows_action(state, "apply_patch")

        if not has_approved_action(repo_path, state.request_id, "apply_patch"):
            console.print(
                "[red]Cannot apply patch.[/red] "
                "The `apply_patch` action has not been approved."
            )
            raise typer.Exit(code=1)

        result = apply_available_patch(repo_path, state)

        if isinstance(result, Path):
            relative_output_path = result.relative_to(repo_path)

            if str(relative_output_path) not in state.changed_files:
                state.changed_files.append(str(relative_output_path))

            console.print("[green]Patch note created.[/green]")
            console.print(f"Created: {relative_output_path}")
        else:
            for changed_file in result.changed_files:
                if changed_file not in state.changed_files:
                    state.changed_files.append(changed_file)

            console.print("[green]Unified diff patch applied.[/green]")
            console.print(f"Patch file: {result.patch_path}")

        state.pending_action = None
        state.pending_approval = False
        state.mark_completed("apply_patch")

        save_state(state)
        update_delivery_markdown(state)

        console.print("[green]Apply patch workflow completed.[/green]")

    @app.command("generate-fix-patch")
    def generate_fix_patch_command(
        repo: str = typer.Option(".", help="Path to the local repository."),
    ):
        repo_path = resolve_repo_path(repo)
        state = load_state(repo_path)

        attempt = generate_controlled_fix_patch(repo_path, state)

        if attempt.status == "generated":
            state.mark_completed("generate_fix_patch")

        save_state(state)
        update_delivery_markdown(state)

        if attempt.status == "generated":
            console.print("[green]Controlled fix patch generated.[/green]")
            console.print(f"Patch: {attempt.generated_patch_path}")
            console.print("[yellow]Waiting for approval:[/yellow] apply_patch")
            return

        console.print("[yellow]Fix patch was not generated successfully.[/yellow]")
        console.print(f"Status: {attempt.status}")

        if attempt.error:
            console.print(f"Error: {attempt.error}")

        raise typer.Exit(code=1)
