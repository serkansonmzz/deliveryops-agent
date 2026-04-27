from pathlib import Path
import subprocess

from app.schemas.delivery_state import DeliveryState
from app.tools.release_judge_tools import (
    evaluate_release_readiness,
    apply_readiness_result_to_state,
)


def init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, check=True)


def test_readiness_blocks_when_patch_not_applied(tmp_path: Path):
    init_git_repo(tmp_path)

    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Add readiness check",
    )

    result = evaluate_release_readiness(tmp_path, state)

    assert result.status == "blocked"
    assert any("Patch has not been applied" in blocker for blocker in result.blockers)


def test_readiness_blocks_when_tests_failed(tmp_path: Path):
    init_git_repo(tmp_path)

    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Add readiness check",
        test_status="failed",
        test_output="AssertionError: assert 1 == 2",
    )
    state.mark_completed("apply_patch")
    state.mark_completed("detect_tests")
    state.mark_completed("run_tests")

    result = evaluate_release_readiness(tmp_path, state)

    assert result.status == "blocked"
    assert any("Tests are currently failing" in blocker for blocker in result.blockers)


def test_readiness_needs_review_when_tests_not_detected(tmp_path: Path):
    init_git_repo(tmp_path)

    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Add readiness check",
        test_status="not_detected",
    )
    state.mark_completed("apply_patch")
    state.mark_completed("detect_tests")

    result = evaluate_release_readiness(tmp_path, state)

    assert result.status == "needs_review"
    assert any("No test command was detected" in warning for warning in result.warnings)


def test_readiness_ready_when_core_evidence_exists(tmp_path: Path):
    init_git_repo(tmp_path)

    readme = tmp_path / "README.md"
    readme.write_text("# Test Project\n", encoding="utf-8")

    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "chore: initial commit"], cwd=tmp_path, check=True)

    readme.write_text("# Test Project\n\nReadiness docs.\n", encoding="utf-8")

    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Add readiness check",
        github_issue_url="https://github.com/test/repo/issues/1",
        branch_name="feature/readiness-check",
        test_status="passed",
        commit_message="feat: add readiness check",
        commit_hash="abc1234",
    )
    state.mark_completed("apply_patch")
    state.mark_completed("detect_tests")
    state.mark_completed("run_tests")
    state.mark_completed("commit_changes")

    result = evaluate_release_readiness(tmp_path, state)
    assert result.status == "ready"
    assert result.blockers == []


def test_apply_readiness_result_to_state(tmp_path: Path):
    init_git_repo(tmp_path)

    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Add readiness check",
    )

    result = evaluate_release_readiness(tmp_path, state)
    apply_readiness_result_to_state(state, result)

    assert state.readiness_status == result.status
    assert state.readiness_risk_level == result.risk_level
    assert "release_readiness_check" in state.completed_steps
