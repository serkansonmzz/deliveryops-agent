from pathlib import Path

from app.schemas.delivery_state import DeliveryState
from app.tools.release_candidate_tools import (
    build_mvp_release_notes,
    write_mvp_release_notes,
    apply_mvp_release_candidate_state,
)


def test_build_mvp_release_notes():
    state = DeliveryState(
        request_id="req_test",
        repo_path="/tmp/repo",
        original_request="Prepare MVP release candidate",
        mvp_release_status="release_candidate",
    )

    notes = build_mvp_release_notes(state)

    assert "DeliveryOps Agent MVP Release Notes" in notes
    assert "Core Capabilities" in notes
    assert "Policy profiles" in notes
    assert "Controlled fix patch loop" in notes


def test_write_mvp_release_notes(tmp_path: Path):
    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Prepare MVP release candidate",
    )

    notes_path = write_mvp_release_notes(tmp_path, state)

    assert notes_path.exists()
    assert notes_path.name == "MVP_RELEASE_NOTES.md"
    assert "DeliveryOps Agent MVP Release Notes" in notes_path.read_text(encoding="utf-8")


def test_apply_mvp_release_candidate_state(tmp_path: Path):
    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Prepare MVP release candidate",
    )

    notes_path = tmp_path / "docs" / "MVP_RELEASE_NOTES.md"
    notes_path.parent.mkdir()
    notes_path.write_text("# Notes\n", encoding="utf-8")

    apply_mvp_release_candidate_state(state, notes_path, tmp_path)

    assert state.mvp_release_status == "release_candidate"
    assert state.mvp_release_notes_path == "docs/MVP_RELEASE_NOTES.md"
    assert state.mvp_release_checklist
    assert "mvp_release_candidate_hardening" in state.completed_steps
