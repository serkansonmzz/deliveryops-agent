from pathlib import Path

from app.schemas.delivery_state import DeliveryState
from app.tools.repo_context_tools import collect_repo_context


def test_collect_repo_context(tmp_path: Path):
    file_path = tmp_path / "README.md"
    file_path.write_text("# Test Project\n", encoding="utf-8")

    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Update README documentation",
        likely_files=["README.md"],
        implementation_plan=["Update README"],
        architecture_review_summary="README is likely affected.",
    )

    context = collect_repo_context(tmp_path, state)

    assert context["request"] == "Update README documentation"
    assert context["likely_files"] == ["README.md"]
    assert context["files"][0]["path"] == "README.md"
    assert "# Test Project" in context["files"][0]["content"]
    assert "dev_patch_context" in context
    assert "README.md" in context["dev_patch_context"]
    assert state.dev_context_status == "prepared"
    assert state.dev_context_selected_files == ["README.md"]


def test_collect_repo_context_includes_related_tests(tmp_path: Path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("print('hello')\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_app.py").write_text(
        "def test_app():\n    assert True\n",
        encoding="utf-8",
    )
    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Update app behavior",
        implementation_plan_target_files=["src/app.py"],
        repo_source_test_map={"src/app.py": ["tests/test_app.py"]},
        implementation_plan=["Update app behavior"],
        architecture_review_summary="Source change.",
    )

    context = collect_repo_context(tmp_path, state)

    paths = [file["path"] for file in context["files"]]
    assert "src/app.py" in paths
    assert "tests/test_app.py" in paths
    assert state.dev_context_related_tests == ["tests/test_app.py"]
