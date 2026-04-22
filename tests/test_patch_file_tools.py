import subprocess
from pathlib import Path

from app.tools.patch_file_tools import (
    get_default_patch_path,
    has_generated_patch,
    apply_unified_diff_patch,
)


def init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, check=True)


def test_has_generated_patch_false(tmp_path: Path):
    init_git_repo(tmp_path)

    assert has_generated_patch(tmp_path) is False


def test_get_default_patch_path(tmp_path: Path):
    patch_path = get_default_patch_path(tmp_path)

    assert patch_path == tmp_path / ".deliveryops" / "generated.patch"


def test_apply_unified_diff_patch(tmp_path: Path):
    init_git_repo(tmp_path)

    readme = tmp_path / "README.md"
    readme.write_text("# Test Project\n", encoding="utf-8")

    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "chore: initial commit"], cwd=tmp_path, check=True)

    workspace = tmp_path / ".deliveryops"
    workspace.mkdir()

    patch_path = workspace / "generated.patch"
    patch_path.write_text(
        """diff --git a/README.md b/README.md
index 0795791..b7b38df 100644
--- a/README.md
+++ b/README.md
@@ -1 +1,3 @@
 # Test Project
+
+Generated patch applied.
""",
        encoding="utf-8",
    )

    result = apply_unified_diff_patch(tmp_path, patch_path)

    assert result.applied is True
    assert "README.md" in result.changed_files
    assert "Generated patch applied." in readme.read_text(encoding="utf-8")