from pathlib import Path

from app.schemas.delivery_state import DeliveryState
from app.tools.delivery_report_tools import (
    build_progress_comment,
    build_final_report,
    write_final_report,
)


def test_build_progress_comment():
    state = DeliveryState(
        request_id="req_test",
        repo_path="/tmp/repo",
        original_request="Add final report support",
        branch_name="feature/final-report",
        commit_hash="abc1234",
        pr_url="https://github.com/test/repo/pull/1",
        changed_files=["src/app/main.py"],
    )
    state.mark_completed("open_draft_pr")

    comment = build_progress_comment(state)

    assert "DeliveryOps Progress Update" in comment
    assert "req_test" in comment
    assert "abc1234" in comment
    assert "src/app/main.py" in comment


def test_build_final_report():
    state = DeliveryState(
        request_id="req_test",
        repo_path="/tmp/repo",
        original_request="Add final report support",
        github_issue_url="https://github.com/test/repo/issues/1",
        pr_url="https://github.com/test/repo/pull/1",
        commit_hash="abc1234",
        committed_files=["src/app/main.py"],
        commit_message="feat: add final report support",
        test_command="uv run pytest -q",
        test_status="passed",
        test_exit_code=0,
        ci_status="no_checks",
        ci_summary="No GitHub checks are configured.",
        readiness_status="ready",
        readiness_risk_level="low",
        dev_context_selected_files=["src/app/main.py"],
        dev_context_related_tests=["tests/test_main.py"],
    )
    state.mark_completed("apply_patch")

    report = build_final_report(state)

    assert report.title == "DeliveryOps Final Report"
    assert "Add final report support" in report.body
    assert "abc1234" in report.body
    assert "src/app/main.py" in report.body
    assert "Test Status: `passed`" in report.body
    assert "CI Status: `no_checks`" in report.body
    assert "Readiness Status: `ready`" in report.body
    assert "tests/test_main.py" in report.body


def test_build_final_report_avoids_double_numbered_plan_steps():
    state = DeliveryState(
        request_id="req_test",
        repo_path="/tmp/repo",
        original_request="Add final report support",
        implementation_plan=["1. Review context"],
    )

    report = build_final_report(state)

    assert "1. Review context" in report.body
    assert "1. 1. Review context" not in report.body


def test_write_final_report(tmp_path: Path):
    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Add final report support",
    )

    report = build_final_report(state)
    report_path = write_final_report(tmp_path, report)

    assert report_path.exists()
    assert report_path.name == "FINAL_REPORT.md"
    assert "DeliveryOps Final Report" in report_path.read_text(encoding="utf-8")
