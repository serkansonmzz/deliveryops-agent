import pytest

from app.adapters.test_runner_adapter import (
    is_safe_test_command,
    parse_command,
    run_test_command,
)


def test_parse_command():
    assert parse_command("uv run pytest -q") == ("uv", "run", "pytest", "-q")


def test_is_safe_test_command_accepts_allowlisted_commands():
    assert is_safe_test_command("uv run pytest -q") is True
    assert is_safe_test_command("python -m pytest -q") is True
    assert is_safe_test_command("npm test") is True


def test_is_safe_test_command_rejects_unsafe_commands():
    assert is_safe_test_command("rm -rf .") is False
    assert is_safe_test_command("pytest -q; rm -rf .") is False


def test_run_test_command_rejects_unsafe_command(tmp_path):
    with pytest.raises(RuntimeError):
        run_test_command(tmp_path, "python -c 'print(123)'")
