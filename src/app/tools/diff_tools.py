import difflib
from pathlib import Path


def build_unified_diff(
    file_path: str,
    before: str,
    after: str,
) -> str:
    before_lines = before.splitlines(keepends=True)
    after_lines = after.splitlines(keepends=True)

    diff_lines = difflib.unified_diff(
        before_lines,
        after_lines,
        fromfile=f"a/{file_path}",
        tofile=f"b/{file_path}",
    )

    return "".join(diff_lines)


def write_generated_patch(repo_path: Path, patch_content: str) -> Path:
    workspace = repo_path / ".deliveryops"
    workspace.mkdir(exist_ok=True)

    patch_path = workspace / "generated.patch"
    patch_path.write_text(patch_content, encoding="utf-8")

    return patch_path