from pathlib import Path
import subprocess

from app.schemas.delivery_state import DeliveryState
from app.tools.auto_continue_tools import run_safe_auto_continue


def init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, check=True)


def test_auto_continue_generates_commit_message(tmp_path: Path):
    init_git_repo(tmp_path)

    readme = tmp_path / "README.md"
    readme.write_text("# Test Project\n", encoding="utf-8")

    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "chore: initial commit"], cwd=tmp_path, check=True)

    readme.write_text("# Test Project\n\nNew docs.\n", encoding="utf-8")

    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Update README documentation",
    )

    state.mark_completed("apply_patch")
    state.mark_completed("detect_tests")

    result = run_safe_auto_continue(tmp_path, state)

    assert "generate_commit_message" in result.executed_actions
    assert state.commit_message is not None
    assert state.pending_action == "git_commit"
    assert state.pending_approval is True


def test_auto_continue_stops_when_approval_required(tmp_path: Path):
    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Update README documentation",
    )

    state.mark_completed("apply_patch")
    state.mark_completed("detect_tests")
    state.mark_completed("generate_commit_message")

    result = run_safe_auto_continue(tmp_path, state)

    assert result.executed_actions == []
    assert result.stopped_at_action == "approve_git_commit"


def test_auto_continue_generates_final_report(tmp_path: Path):
    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Update README documentation",
    )

    for step in [
        "apply_patch",
        "detect_tests",
        "generate_commit_message",
        "commit_changes",
        "push_branch",
        "open_draft_pr",
        "check_ci_status",
        "comment_progress",
    ]:
        state.mark_completed(step)

    result = run_safe_auto_continue(tmp_path, state)

    assert "final_report" in result.executed_actions
    assert state.final_report_status == "generated"

    final_report_path = tmp_path / ".deliveryops" / "FINAL_REPORT.md"

    assert final_report_path.exists()