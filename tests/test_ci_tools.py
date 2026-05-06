from app.schemas.delivery_state import DeliveryState
from app.adapters.command_result import CommandResult
from app.schemas.ci_status import CIStatusResult, CICheckResult
from app.tools import ci_tools
from app.tools.ci_tools import (
    parse_pr_checks_output,
    parse_pr_checks_json_output,
    apply_ci_status_to_state,
    normalize_check_state,
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
        error="ci error",
    )

    apply_ci_status_to_state(state, result)

    assert state.ci_status == "failed"
    assert state.ci_error == "ci error"
    assert state.ci_check_count == 3
    assert "tests fail" in state.ci_failed_checks
    assert "lint pending" in state.ci_pending_checks
    assert "check_ci_status" in state.completed_steps


def test_normalize_check_state():
    assert normalize_check_state("completed", "success") == "passed"
    assert normalize_check_state("completed", "failure") == "failed"
    assert normalize_check_state("in_progress", None) == "pending"
    assert normalize_check_state("queued", None) == "pending"


def test_parse_pr_checks_json_output_passed():
    raw = """
[
  {"name": "build", "state": "completed", "conclusion": "success", "link": "https://example.com/build"},
  {"name": "tests", "state": "completed", "conclusion": "success", "link": "https://example.com/tests"}
]
"""

    result = parse_pr_checks_json_output(raw)

    assert result.status == "passed"
    assert len(result.checks) == 2
    assert result.checks[0].url == "https://example.com/build"


def test_parse_pr_checks_json_output_failed():
    raw = """
[
  {"name": "build", "state": "completed", "conclusion": "success"},
  {"name": "tests", "state": "completed", "conclusion": "failure"}
]
"""

    result = parse_pr_checks_json_output(raw)

    assert result.status == "failed"
    assert any(check.name == "tests" for check in result.checks)


def test_parse_pr_checks_json_output_pending():
    raw = """
[
  {"name": "build", "state": "in_progress", "conclusion": null}
]
"""

    result = parse_pr_checks_json_output(raw)

    assert result.status == "pending"


def test_parse_pr_checks_json_output_invalid_json():
    result = parse_pr_checks_json_output("not json")

    assert result.status == "unknown"
    assert result.error


def test_check_pull_request_ci_status_returns_no_pr(monkeypatch, tmp_path):
    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Test CI hardening",
        pushed_branch="feature/test",
    )

    monkeypatch.setattr(ci_tools, "ensure_gh_authenticated", lambda repo_path: None)
    monkeypatch.setattr(
        ci_tools,
        "get_current_branch_pr_json",
        lambda branch, repo_path: CommandResult(
            args=["gh", "pr", "view"],
            return_code=1,
            stdout="",
            stderr="no pull requests found",
        ),
    )

    result = ci_tools.check_pull_request_ci_status(tmp_path, state)

    assert result.status == "no_pr"
    assert result.error
