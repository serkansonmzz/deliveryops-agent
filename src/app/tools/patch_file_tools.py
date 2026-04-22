import subprocess
from pathlib import Path

from pydantic import BaseModel


class PatchApplyResult(BaseModel):
    applied: bool
    patch_path: str
    changed_files: list[str]
    stdout: str = ""
    stderr: str = ""


def get_default_patch_path(repo_path: Path) -> Path:
    return repo_path / ".deliveryops" / "generated.patch"


def has_generated_patch(repo_path: Path) -> bool:
    return get_default_patch_path(repo_path).exists()


def run_git_apply_check(repo_path: Path, patch_path: Path) -> None:
    result = subprocess.run(
        ["git", "apply", "--check", str(patch_path)],
        cwd=repo_path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Patch validation failed.\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )


def apply_unified_diff_patch(repo_path: Path, patch_path: Path) -> PatchApplyResult:
    if not patch_path.exists():
        raise FileNotFoundError(f"Patch file not found: {patch_path}")

    run_git_apply_check(repo_path, patch_path)

    result = subprocess.run(
        ["git", "apply", str(patch_path)],
        cwd=repo_path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Patch application failed.\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )

    changed_files = get_changed_files(repo_path)

    return PatchApplyResult(
        applied=True,
        patch_path=str(patch_path.relative_to(repo_path)),
        changed_files=changed_files,
        stdout=result.stdout.strip(),
        stderr=result.stderr.strip(),
    )


def get_changed_files(repo_path: Path) -> list[str]:
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=repo_path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    files: list[str] = []

    for line in result.stdout.splitlines():
        if not line.strip():
            continue

        # Git short status format: " M path", "?? path", "A  path"
        files.append(line[3:].strip())

    return sorted(set(files))