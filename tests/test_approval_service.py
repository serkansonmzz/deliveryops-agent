from pathlib import Path
import subprocess

from app.schemas.delivery_state import DeliveryState
from app.services.approval_service import get_or_build_approval_status
from app.state_store import ensure_workspace, save_state


def init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, stdout=subprocess.PIPE)


def make_state(repo_path: Path, **kwargs) -> DeliveryState:
    state = DeliveryState(
        request_id="req_test",
        repo_path=str(repo_path),
        original_request="Approval service layer",
        **kwargs,
    )
    ensure_workspace(repo_path)
    save_state(state)
    return state


def test_approval_status_service_returns_none_without_pending_approval(tmp_path: Path):
    init_git_repo(tmp_path)
    make_state(tmp_path)

    result = get_or_build_approval_status(tmp_path)

    assert result.status == "none"


def test_approval_status_service_builds_pending_request(tmp_path: Path):
    init_git_repo(tmp_path)
    make_state(
        tmp_path,
        pending_action="git_commit",
        pending_approval=True,
        changed_files=["README.md"],
    )

    result = get_or_build_approval_status(tmp_path)

    assert result.status == "pending"
    assert result.details.get("action") == "git_commit"
    assert "commit" in str(result.details.get("command"))
