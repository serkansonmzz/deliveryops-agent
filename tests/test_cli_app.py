from typer.testing import CliRunner

from app.cli.app import app


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
