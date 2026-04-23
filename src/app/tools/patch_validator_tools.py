from pathlib import Path

from app.tools.patch_file_tools import run_git_apply_check


def validate_unified_diff(patch_text: str) -> list[str]:
    errors: list[str] = []
    stripped = patch_text.lstrip()

    if not stripped:
        return ["Patch is empty."]

    if not (
        stripped.startswith("diff --git ")
        or stripped.startswith("--- a/")
    ):
        errors.append("Patch must start with 'diff --git ' or '--- a/'.")

    if "--- " not in patch_text:
        errors.append("Patch is missing the '---' header.")

    if "+++ " not in patch_text:
        errors.append("Patch is missing the '+++' header.")

    if "@@ " not in patch_text:
        errors.append("Patch is missing a hunk header ('@@').")

    return errors


def validate_unified_diff_or_raise(patch_text: str) -> None:
    errors = validate_unified_diff(patch_text)

    if errors:
        bullet_list = "\n".join(f"- {error}" for error in errors)
        raise RuntimeError(f"Invalid unified diff patch:\n{bullet_list}")


def validate_patch_can_apply_or_raise(repo_path: Path, patch_text: str) -> None:
    workspace = repo_path / ".deliveryops"
    workspace.mkdir(exist_ok=True)

    candidate_path = workspace / "candidate.patch"
    rejected_path = workspace / "rejected.patch"
    error_path = workspace / "patch_validation_error.txt"

    candidate_path.write_text(patch_text, encoding="utf-8")

    try:
        run_git_apply_check(repo_path, candidate_path)
    except RuntimeError as exc:
        rejected_path.write_text(patch_text, encoding="utf-8")
        error_path.write_text(str(exc), encoding="utf-8")
        raise RuntimeError(
            "Agent patch failed `git apply --check`. "
            "The patch was saved to `.deliveryops/rejected.patch` "
            "and the validation error was saved to `.deliveryops/patch_validation_error.txt`."
        ) from exc
    finally:
        if candidate_path.exists():
            candidate_path.unlink()