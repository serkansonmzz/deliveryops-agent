import subprocess
from pathlib import Path

from app.adapters.command_result import CommandResult


def run_process(
    args: list[str],
    cwd: Path,
    timeout_seconds: int | None = None,
) -> CommandResult:
    result = subprocess.run(
        args,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout_seconds,
        check=False,
    )

    return CommandResult(
        args=args,
        return_code=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )


def run_process_or_raise(
    args: list[str],
    cwd: Path,
    timeout_seconds: int | None = None,
) -> CommandResult:
    result = run_process(
        args=args,
        cwd=cwd,
        timeout_seconds=timeout_seconds,
    )

    if not result.ok:
        raise RuntimeError(
            f"Command failed: {' '.join(args)}\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

    return result
