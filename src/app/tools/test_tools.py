from pathlib import Path

from app.adapters.test_runner_adapter import (
    is_safe_test_command,
    parse_command,
    run_test_command,
)
from app.schemas.test_run_result import TestRunResult


def detect_test_command(repo_path: Path) -> str | None:
    tests_dir = repo_path / "tests"
    pyproject = repo_path / "pyproject.toml"
    uv_lock = repo_path / "uv.lock"
    package_json = repo_path / "package.json"

    if tests_dir.exists() and tests_dir.is_dir():
        if pyproject.exists() and uv_lock.exists():
            return "uv run pytest -q"

        if pyproject.exists():
            return "python -m pytest -q"

        return "pytest -q"

    if package_json.exists():
        return "npm test"

    return None
def summarize_test_output(exit_code: int, stdout: str, stderr: str) -> str:
    if exit_code == 0:
        return "Tests passed successfully."

    combined = "\n".join(part for part in [stdout, stderr] if part.strip())
    lines = combined.splitlines()
    tail = "\n".join(lines[-20:]) if lines else "No test output captured."

    return f"Tests failed with exit code {exit_code}.\n\nLast output lines:\n{tail}"


def run_safe_test_command(
    repo_path: Path,
    command: str,
    timeout_seconds: int = 120,
) -> TestRunResult:
    result = run_test_command(
        repo_path=repo_path,
        command=command,
        timeout_seconds=timeout_seconds,
    )

    status = "passed" if result.return_code == 0 else "failed"
    summary = summarize_test_output(
        exit_code=result.return_code,
        stdout=result.stdout,
        stderr=result.stderr,
    )

    return TestRunResult(
        command=command,
        status=status,
        exit_code=result.return_code,
        stdout=result.stdout.strip(),
        stderr=result.stderr.strip(),
        summary=summary,
    )
