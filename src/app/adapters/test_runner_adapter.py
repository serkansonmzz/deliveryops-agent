import shlex
from pathlib import Path

from app.adapters.command_result import CommandResult
from app.adapters.process_adapter import run_process


SAFE_TEST_COMMANDS = {
    ("uv", "run", "pytest", "-q"),
    ("python", "-m", "pytest", "-q"),
    ("pytest", "-q"),
    ("npm", "test"),
    ("pnpm", "test"),
    ("yarn", "test"),
}


def parse_command(command: str) -> tuple[str, ...]:
    return tuple(shlex.split(command))


def is_safe_test_command(command: str) -> bool:
    return parse_command(command) in SAFE_TEST_COMMANDS


def run_test_command(
    repo_path: Path,
    command: str,
    timeout_seconds: int = 120,
) -> CommandResult:
    if not is_safe_test_command(command):
        raise RuntimeError(f"Refusing to run unsafe test command: {command}")

    return run_process(
        args=list(parse_command(command)),
        cwd=repo_path,
        timeout_seconds=timeout_seconds,
    )
