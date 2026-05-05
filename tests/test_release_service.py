from pathlib import Path
import subprocess

from app.schemas.delivery_state import DeliveryState
from app.services.release_service import (
    generate_final_report,
    generate_mvp_release_notes,
    run_readiness_check,
)
from app.state_store import ensure_workspace, save_state


def init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, check=True)


def make_state(repo_path: Path, **kwargs) -> DeliveryState:
    state = DeliveryState(
        request_id="req_test",
        repo_path=str(repo_path),
        original_request="Release service layer",
        **kwargs,
    )
    ensure_workspace(repo_path)
    save_state(state)
    return state


def test_generate_final_report_service(tmp_path: Path):
    init_git_repo(tmp_path)
    make_state(tmp_path)

    result = generate_final_report(tmp_path)

    assert result.status == "generated"
    assert result.details.get("report_path") == ".deliveryops/FINAL_REPORT.md"
    assert (tmp_path / ".deliveryops" / "FINAL_REPORT.md").exists()


def test_generate_mvp_release_notes_service(tmp_path: Path):
    init_git_repo(tmp_path)
    make_state(tmp_path)

    result = generate_mvp_release_notes(tmp_path)

    assert result.status == "generated"
    assert result.details.get("release_notes") == "docs/MVP_RELEASE_NOTES.md"
    assert (tmp_path / "docs" / "MVP_RELEASE_NOTES.md").exists()


def test_run_readiness_check_service_blocks_without_patch(tmp_path: Path):
    init_git_repo(tmp_path)
    make_state(tmp_path)

    result = run_readiness_check(tmp_path)

    assert result.status == "blocked"
    assert result.exit_code == 1
