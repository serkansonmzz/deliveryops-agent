from pathlib import Path

from app.schemas.delivery_state import DeliveryState
from app.tools.apply_patch_tools import (
    build_patch_note_content,
    apply_patch_note,
)


def test_build_patch_note_content():
    state = DeliveryState(
        request_id="req_test",
        repo_path="/tmp/repo",
        original_request="Add approval command support.",
        github_issue_url="https://github.com/test/repo/issues/1",
        branch_name="feature/1-test",
        patch_summary="Patch proposal prepared.",
        proposed_changes=["Inspect files", "Update code"],
    )

    content = build_patch_note_content(state)

    assert "# DeliveryOps Patch Note" in content
    assert "Add approval command support." in content
    assert "Patch proposal prepared." in content
    assert "Inspect files" in content


def test_apply_patch_note(tmp_path: Path):
    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Add approval command support.",
        patch_summary="Patch proposal prepared.",
        proposed_changes=["Inspect files"],
    )

    output_path = apply_patch_note(tmp_path, state)

    assert output_path.exists()

    content = output_path.read_text(encoding="utf-8")

    assert "# DeliveryOps Patch Note" in content
    assert "Add approval command support." in content