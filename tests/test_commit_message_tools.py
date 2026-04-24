from pathlib import Path
import subprocess

from app.schemas.delivery_state import DeliveryState
from app.tools.commit_message_tools import (
    normalize_request_text,
    infer_commit_type,
    summarize_diff,
    build_commit_message_spec,
)


def init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, check=True)


def test_normalize_request_text():
    result = normalize_request_text("  Add Commit Message Generation   ")

    assert result == "add Commit Message Generation"


def test_infer_commit_type_docs():
    commit_type = infer_commit_type(
        request="Update README documentation",
        changed_files=["README.md"],
    )

    assert commit_type == "docs"


def test_infer_commit_type_fix():
    commit_type = infer_commit_type(
        request="Fix branch validation bug",
        changed_files=["src/app/main.py"],
    )

    assert commit_type == "fix"


def test_summarize_diff():
    diff = """diff --git a/README.md b/README.md
--- a/README.md
+++ b/README.md
@@ -1 +1,2 @@
 # Test
+New line
"""

    summary = summarize_diff(diff, ["README.md"])

    assert "README.md" in summary
    assert "Added lines: 1" in summary
    assert "Removed lines: 0" in summary


def test_build_commit_message_spec(tmp_path: Path):
    init_git_repo(tmp_path)

    readme = tmp_path / "README.md"
    readme.write_text("# Test Project\n", encoding="utf-8")

    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "chore: initial commit"], cwd=tmp_path, check=True)

    readme.write_text("# Test Project\n\nNew documentation.\n", encoding="utf-8")

    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Update README documentation",
        github_issue_url="https://github.com/test/repo/issues/1",
    )

    spec = build_commit_message_spec(tmp_path, state)

    assert spec.subject.startswith("docs:")
    assert "README.md" in spec.changed_files
    assert "Added lines:" in spec.diff_summary