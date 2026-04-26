import shlex
import subprocess
from pathlib import Path

from app.schemas.test_run_result import TestRunResult


SAFE_TEST_COMMANDS = {
    ("uv", "run", "pytest", "-q"),
    ("python", "-m", "pytest", "-q"),
    ("pytest", "-q"),
    ("npm", "test"),
    ("pnpm", "test"),
    ("yarn", "test"),
}


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


def parse_command(command: str) -> tuple[str, ...]:
    return tuple(shlex.split(command))


def is_safe_test_command(command: str) -> bool:
    return parse_command(command) in SAFE_TEST_COMMANDS


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
    if not is_safe_test_command(command):
        raise RuntimeError(f"Refusing to run unsafe test command: {command}")

    args = list(parse_command(command))

    result = subprocess.run(
        args,
        cwd=repo_path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout_seconds,
        check=False,
    )

    status = "passed" if result.returncode == 0 else "failed"
    summary = summarize_test_output(
        exit_code=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )

    return TestRunResult(
        command=command,
        status=status,
        exit_code=result.returncode,
        stdout=result.stdout.strip(),
        stderr=result.stderr.strip(),
        summary=summary,
    )
