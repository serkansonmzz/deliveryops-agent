from pathlib import Path
import subprocess

from app.schemas.delivery_state import DeliveryState
from app.services.workflow_service import get_workflow_status
from app.state_store import ensure_workspace, save_state


def init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, stdout=subprocess.PIPE)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=path,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=path,
        check=True,
    )


def test_get_workflow_status_returns_service_result(tmp_path: Path):
    init_git_repo(tmp_path)
    ensure_workspace(tmp_path)
    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Test workflow service",
    )
    save_state(state)

    result = get_workflow_status(tmp_path)

    assert result.status
    assert "current_step" in result.details
    assert "safe_to_run" in result.details
    assert "requires_approval" in result.details
