from typer.testing import CliRunner

from app.cli import patch_commands
from app.cli.app import app
from app.schemas.delivery_state import DeliveryState


runner = CliRunner()


def test_cli_help_loads():
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "DeliveryOps Agent" in result.output


def test_core_commands_are_registered():
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0

    expected_commands = [
        "run",
        "continue",
        "auto-continue",
        "analyze-repo",
        "architecture-review",
        "implementation-plan",
        "approval-status",
        "apply-patch",
        "detect-tests",
        "run-tests",
        "readiness-check",
        "final-report",
        "policy-status",
        "agent-roles",
    ]

    for command in expected_commands:
        assert command in result.output


def test_dev_generate_patch_prints_progress(monkeypatch, tmp_path):
    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Update README docs.",
    )
    patch_path = tmp_path / ".deliveryops" / "generated.patch"
    patch_path.parent.mkdir()
    patch_path.write_text("", encoding="utf-8")

    monkeypatch.setattr(patch_commands, "resolve_repo_path", lambda repo: tmp_path)
    monkeypatch.setattr(patch_commands, "load_state", lambda repo_path: state)
    monkeypatch.setattr(
        patch_commands,
        "generate_patch_with_agent",
        lambda repo_path, state, progress=None: patch_path,
    )
    monkeypatch.setattr(patch_commands, "save_state", lambda state: None)
    monkeypatch.setattr(patch_commands, "update_delivery_markdown", lambda state: None)

    result = runner.invoke(app, ["dev-generate-patch", "--repo", str(tmp_path)])

    assert result.exit_code == 0
    assert "Preparing Dev Agent context" in result.output
    assert "Working on Dev Agent patch generation" in result.output
    assert "Generating and validating patch with Dev Agent" in result.output
    assert "Agent patch generated" in result.output


def test_run_help_includes_fast_mode():
    result = runner.invoke(app, ["run", "--help"])

    assert result.exit_code == 0
    assert "--fast" in result.output
    assert "--no-llm-planning" in result.output
