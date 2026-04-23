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