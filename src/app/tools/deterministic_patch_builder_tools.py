from pathlib import Path

from app.schemas.agent_patch_response import FileEditIntent
from app.tools.dev_context_tools import is_binary_like, is_blocked_file
from app.tools.diff_tools import build_unified_diff


SUPPORTED_EDIT_TYPES = {
    "create_file",
    "replace_text",
    "append_after",
    "append_to_file",
}


def _safe_repo_path(repo_path: Path, relative_path: str) -> Path:
    if is_blocked_file(relative_path):
        raise RuntimeError(f"Blocked file edit target: {relative_path}")

    if is_binary_like(relative_path):
        raise RuntimeError(f"Binary-like file edit target is not supported: {relative_path}")

    repo_root = repo_path.resolve()
    full_path = (repo_path / relative_path).resolve()
    try:
        full_path.relative_to(repo_root)
    except ValueError as exc:
        raise RuntimeError(f"Path traversal is not allowed: {relative_path}") from exc

    return full_path


def _read_existing_file(repo_path: Path, relative_path: str) -> str:
    full_path = _safe_repo_path(repo_path, relative_path)
    if not full_path.exists() or not full_path.is_file():
        raise RuntimeError(f"File does not exist for edit: {relative_path}")
    return full_path.read_text(encoding="utf-8", errors="replace")


def _ensure_trailing_newline(content: str) -> str:
    if content and not content.endswith("\n"):
        return content + "\n"
    return content


def apply_file_edit_intent(
    repo_path: Path,
    edit: FileEditIntent,
    current_content: str | None = None,
) -> tuple[str, str, str]:
    if edit.edit_type not in SUPPORTED_EDIT_TYPES:
        raise RuntimeError(f"Unsupported file edit type: {edit.edit_type}")

    _safe_repo_path(repo_path, edit.path)
    content = _ensure_trailing_newline(edit.content)

    if edit.edit_type == "create_file":
        full_path = _safe_repo_path(repo_path, edit.path)
        if full_path.exists() or current_content is not None:
            raise RuntimeError(f"Cannot create file because it already exists: {edit.path}")
        return edit.path, "", content

    before = current_content if current_content is not None else _read_existing_file(repo_path, edit.path)

    if edit.edit_type == "replace_text":
        if not edit.anchor:
            raise RuntimeError(f"replace_text requires anchor for {edit.path}")
        replacement = edit.replacement if edit.replacement is not None else content
        if edit.anchor not in before:
            raise RuntimeError(f"Anchor was not found in {edit.path}")
        after = before.replace(edit.anchor, replacement, 1)
        return edit.path, before, after

    if edit.edit_type == "append_after":
        if not edit.anchor:
            raise RuntimeError(f"append_after requires anchor for {edit.path}")
        if edit.anchor not in before:
            raise RuntimeError(f"Anchor was not found in {edit.path}")
        after = before.replace(edit.anchor, edit.anchor + content, 1)
        return edit.path, before, after

    after = before
    if after and not after.endswith("\n"):
        after += "\n"
    after += content
    return edit.path, before, after


def build_patch_from_file_edits(repo_path: Path, edits: list[FileEditIntent]) -> str:
    if not edits:
        raise RuntimeError("No file edit intents were provided.")

    virtual_files: dict[str, str] = {}

    for edit in edits:
        current_content = virtual_files.get(edit.path)
        path, _, after = apply_file_edit_intent(repo_path, edit, current_content)
        virtual_files[path] = after

    patches: list[str] = []
    for path, after in virtual_files.items():
        full_path = _safe_repo_path(repo_path, path)
        before = (
            full_path.read_text(encoding="utf-8", errors="replace")
            if full_path.exists() and full_path.is_file()
            else ""
        )
        patch = build_unified_diff(path, before, after)
        if patch:
            patches.append(patch)

    patch_text = "\n".join(patches)
    if not patch_text.strip():
        raise RuntimeError("File edit intents did not produce any patch changes.")
    return patch_text
