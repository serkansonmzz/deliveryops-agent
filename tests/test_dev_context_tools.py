from pathlib import Path

from app.schemas.delivery_state import DeliveryState
from app.tools.dev_context_tools import (
    build_dev_patch_context,
    collect_related_tests,
    is_binary_like,
    is_blocked_file,
    safe_read_context_file,
    select_dev_context_files,
)


def test_is_blocked_file_detects_env_and_secrets():
    assert is_blocked_file(".env") is True
    assert is_blocked_file("config/secrets.yml") is True
    assert is_blocked_file("src/app/main.py") is False


def test_is_binary_like_detects_binary_suffixes():
    assert is_binary_like("docs/file.pdf") is True
    assert is_binary_like("image.png") is True
    assert is_binary_like("README.md") is False


def test_safe_read_context_file_blocks_env_file(tmp_path: Path):
    (tmp_path / ".env").write_text("SECRET=value\n", encoding="utf-8")

    content = safe_read_context_file(tmp_path, ".env")

    assert content is None


def test_safe_read_context_file_rejects_path_traversal(tmp_path: Path):
    outside_file = tmp_path.parent / "outside_context.txt"
    outside_file.write_text("outside\n", encoding="utf-8")

    content = safe_read_context_file(tmp_path, "../outside_context.txt")

    assert content is None


def test_safe_read_context_file_reads_text_file(tmp_path: Path):
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")

    content = safe_read_context_file(tmp_path, "README.md")

    assert content == "# Demo\n"


def test_safe_read_context_file_truncates_large_text_file(tmp_path: Path):
    (tmp_path / "README.md").write_text("a" * 21_000, encoding="utf-8")

    content = safe_read_context_file(tmp_path, "README.md")

    assert content is not None
    assert "[TRUNCATED: file exceeded context limit]" in content
    assert len(content) < 21_000


def test_collect_related_tests_from_source_test_map():
    state = DeliveryState(
        request_id="req_test",
        repo_path="/tmp/repo",
        original_request="Update test tools",
        repo_source_test_map={
            "src/app/tools/test_tools.py": ["tests/test_test_tools.py"]
        },
    )

    related = collect_related_tests(state, ["src/app/tools/test_tools.py"])

    assert related == ["tests/test_test_tools.py"]


def test_select_dev_context_files_prefers_implementation_targets():
    state = DeliveryState(
        request_id="req_test",
        repo_path="/tmp/repo",
        original_request="Update README docs",
        implementation_plan_target_files=["README.md"],
        likely_files=["docs/WORKFLOW_OVERVIEW.md"],
    )

    selected = select_dev_context_files(state)

    assert selected[0] == "README.md"
    assert "docs/WORKFLOW_OVERVIEW.md" in selected


def test_build_dev_patch_context_reads_selected_files(tmp_path: Path):
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_readme.py").write_text(
        "def test_x():\n    assert True\n",
        encoding="utf-8",
    )
    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Update README docs",
        implementation_plan_target_files=["README.md"],
        repo_source_test_map={"README.md": ["tests/test_readme.py"]},
        architecture_review_summary="Docs-only change.",
        implementation_plan_summary="Update README.",
    )

    context = build_dev_patch_context(tmp_path, state)

    assert context.request == "Update README docs"
    assert context.selected_files
    assert context.selected_files[0].path == "README.md"
    assert "README.md" in context.allowed_target_files
    assert "tests/test_readme.py" in context.related_tests
    assert "Do not modify secrets" in "\n".join(context.patch_rules)
