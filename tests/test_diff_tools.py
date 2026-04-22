from pathlib import Path

from app.tools.diff_tools import build_unified_diff, write_generated_patch


def test_build_unified_diff():
    before = "# Test\n"
    after = "# Test\n\nNew line.\n"

    diff = build_unified_diff(
        file_path="README.md",
        before=before,
        after=after,
    )

    assert "--- a/README.md" in diff
    assert "+++ b/README.md" in diff
    assert "+New line." in diff


def test_write_generated_patch(tmp_path: Path):
    patch_path = write_generated_patch(tmp_path, "patch content")

    assert patch_path.exists()
    assert patch_path.name == "generated.patch"
    assert patch_path.read_text(encoding="utf-8") == "patch content"