from pathlib import Path
import subprocess

import pytest

from app.schemas.agent_patch_response import FileEditIntent
from app.tools.deterministic_patch_builder_tools import build_patch_from_file_edits
from app.tools.patch_validator_tools import validate_patch_can_apply_or_raise


def init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, check=True)


def test_build_patch_from_file_edits_replace_and_append(tmp_path: Path):
    init_git_repo(tmp_path)
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "chore: initial"], cwd=tmp_path, check=True)

    patch = build_patch_from_file_edits(
        tmp_path,
        [
            FileEditIntent(
                path="README.md",
                edit_type="replace_text",
                anchor="# Demo\n",
                content="# Demo App\n",
            ),
            FileEditIntent(
                path="README.md",
                edit_type="append_to_file",
                content="Updated docs.\n",
            ),
        ],
    )

    assert "# Demo App" in patch
    assert "Updated docs" in patch
    validate_patch_can_apply_or_raise(tmp_path, patch)


def test_build_patch_from_file_edits_create_file(tmp_path: Path):
    init_git_repo(tmp_path)
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "chore: initial"], cwd=tmp_path, check=True)

    patch = build_patch_from_file_edits(
        tmp_path,
        [
            FileEditIntent(
                path="src/app.py",
                edit_type="create_file",
                content="def main():\n    return 'ok'\n",
            )
        ],
    )

    assert "src/app.py" in patch
    validate_patch_can_apply_or_raise(tmp_path, patch)


def test_build_patch_from_file_edits_rejects_blocked_and_missing_anchor(tmp_path: Path):
    init_git_repo(tmp_path)
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="Blocked file"):
        build_patch_from_file_edits(
            tmp_path,
            [
                FileEditIntent(
                    path=".env",
                    edit_type="create_file",
                    content="SECRET=value\n",
                )
            ],
        )

    with pytest.raises(RuntimeError, match="Anchor was not found"):
        build_patch_from_file_edits(
            tmp_path,
            [
                FileEditIntent(
                    path="README.md",
                    edit_type="append_after",
                    anchor="missing",
                    content="Nope\n",
                )
            ],
        )
