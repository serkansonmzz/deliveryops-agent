from app.schemas.delivery_state import DeliveryState
from app.schemas.ci_status import CIStatusResult, CICheckResult
from app.tools.ci_tools import (
    parse_pr_checks_output,
    apply_ci_status_to_state,
)


def test_parse_pr_checks_output_passed():
    raw = """
build pass
tests success
"""

    result = parse_pr_checks_output(raw)

    assert result.status == "passed"
    assert result.checks


def test_parse_pr_checks_output_failed():
    raw = """
build pass
tests fail
lint success
"""

    result = parse_pr_checks_output(raw)

    assert result.status == "failed"
    assert any(check.status == "failed" for check in result.checks)


def test_parse_pr_checks_output_pending():
    raw = """
build pending
tests queued
"""

    result = parse_pr_checks_output(raw)

    assert result.status == "pending"
    assert len(result.checks) == 2


def test_parse_pr_checks_output_no_checks():
    result = parse_pr_checks_output("")

    assert result.status == "no_checks"
    assert result.checks == []


def test_apply_ci_status_to_state():
    state = DeliveryState(
        request_id="req_test",
        repo_path="/tmp/repo",
        original_request="Add CI watcher",
    )

    result = CIStatusResult(
        status="failed",
        summary="CI failed.",
        checks=[
            CICheckResult(name="build pass", status="passed"),
            CICheckResult(name="tests fail", status="failed"),
            CICheckResult(name="lint pending", status="pending"),
        ],
        raw_output="raw",
    )

    apply_ci_status_to_state(state, result)

    assert state.ci_status == "failed"
    assert state.ci_check_count == 3
    assert "tests fail" in state.ci_failed_checks
    assert "lint pending" in state.ci_pending_checks
    assert "check_ci_status" in state.completed_steps
