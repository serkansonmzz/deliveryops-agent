from pathlib import Path
import subprocess

import pytest

from app.tools.test_tools import (
    detect_test_command,
    is_safe_test_command,
    run_safe_test_command,
)


def init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, stdout=subprocess.PIPE)


def test_detect_test_command_for_python_tests(tmp_path: Path):
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[project]\nname = 'test-project'\n", encoding="utf-8")

    command = detect_test_command(tmp_path)

    assert command == "python -m pytest -q"


def test_detect_test_command_for_uv_project(tmp_path: Path):
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[project]\nname = 'test-project'\n", encoding="utf-8")

    uv_lock = tmp_path / "uv.lock"
    uv_lock.write_text("", encoding="utf-8")

    command = detect_test_command(tmp_path)

    assert command == "uv run pytest -q"


def test_safe_test_command_accepts_known_commands():
    assert is_safe_test_command("python -m pytest -q") is True
    assert is_safe_test_command("uv run pytest -q") is True
    assert is_safe_test_command("npm test") is True


def test_safe_test_command_rejects_unknown_commands():
    assert is_safe_test_command("rm -rf .") is False
    assert is_safe_test_command("pytest -q; rm -rf .") is False


def test_run_safe_test_command_passes(tmp_path: Path):
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()

    test_file = tests_dir / "test_sample.py"
    test_file.write_text(
        "def test_sample():\n"
        "    assert 1 + 1 == 2\n",
        encoding="utf-8",
    )

    result = run_safe_test_command(tmp_path, "python -m pytest -q")

    assert result.status == "passed"
    assert result.exit_code == 0


def test_run_safe_test_command_rejects_unsafe_command(tmp_path: Path):
    with pytest.raises(RuntimeError):
        run_safe_test_command(tmp_path, "python -c 'print(123)'")
