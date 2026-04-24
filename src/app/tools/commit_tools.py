from pathlib import Path

from app.schemas.commit_result import CommitResult
from app.tools.git_tools import run_git
from app.tools.patch_file_tools import get_changed_files


RUNTIME_PREFIXES = (
    ".deliveryops/",
    ".venv/",
    "__pycache__/",
    ".pytest_cache/",
)


def filter_commit_files(files: list[str]) -> list[str]:
    filtered: list[str] = []

    for file_path in files:
        normalized = file_path.strip()

        if not normalized:
            continue

        if any(normalized.startswith(prefix) for prefix in RUNTIME_PREFIXES):
            continue

        filtered.append(normalized)

    return sorted(set(filtered))


def get_commit_candidate_files(repo_path: Path) -> list[str]:
    changed_files = get_changed_files(repo_path)
    return filter_commit_files(changed_files)


def stage_files_for_commit(repo_path: Path, files: list[str]) -> list[str]:
    commit_files = filter_commit_files(files)

    if not commit_files:
        raise RuntimeError("No commit-safe files found to stage.")

    result = run_git(repo_path, ["add", "--", *commit_files])

    if result.return_code != 0:
        raise RuntimeError(result.stderr)

    return commit_files


def create_git_commit(
    repo_path: Path,
    subject: str,
    body: str | None,
    files: list[str],
) -> CommitResult:
    committed_files = stage_files_for_commit(repo_path, files)

    args = ["commit", "-m", subject]

    if body:
        args.extend(["-m", body])

    result = run_git(repo_path, args)

    if result.return_code != 0:
        raise RuntimeError(result.stderr)

    hash_result = run_git(repo_path, ["rev-parse", "--short", "HEAD"])

    if hash_result.return_code != 0:
        raise RuntimeError(hash_result.stderr)

    return CommitResult(
        commit_hash=hash_result.stdout,
        subject=subject,
        body=body,
        committed_files=committed_files,
    )