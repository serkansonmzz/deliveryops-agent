import pytest

from app.schemas.delivery_state import DeliveryState
from app.tools.fix_patch_loop_tools import (
    can_generate_fix_patch,
    enrich_state_for_fix_patch,
)


def test_cannot_generate_fix_patch_without_failure():
    state = DeliveryState(
        request_id="req_test",
        repo_path="/tmp/repo",
        original_request="Update README",
        test_status="passed",
    )

    allowed, reason = can_generate_fix_patch(state)

    assert allowed is False
    assert "No failed test or CI status" in reason


def test_cannot_generate_fix_patch_before_failure_analysis():
    state = DeliveryState(
        request_id="req_test",
        repo_path="/tmp/repo",
        original_request="Update README",
        test_status="failed",
    )

    allowed, reason = can_generate_fix_patch(state)

    assert allowed is False
    assert "must be analyzed" in reason


def test_cannot_generate_fix_patch_after_max_attempts():
    state = DeliveryState(
        request_id="req_test",
        repo_path="/tmp/repo",
        original_request="Update README",
        test_status="failed",
        fix_patch_attempt_count=3,
        fix_patch_max_attempts=3,
    )
    state.mark_completed("analyze_test_failure")

    allowed, reason = can_generate_fix_patch(state)

    assert allowed is False
    assert "Maximum fix patch attempts" in reason


def test_can_generate_fix_patch_after_failed_tests_are_analyzed():
    state = DeliveryState(
        request_id="req_test",
        repo_path="/tmp/repo",
        original_request="Update README",
        test_status="failed",
        fix_patch_attempt_count=0,
        fix_patch_max_attempts=3,
    )
    state.mark_completed("analyze_test_failure")

    allowed, reason = can_generate_fix_patch(state)

    assert allowed is True
    assert "allowed" in reason


def test_enrich_state_for_fix_patch_uses_failure_context():
    state = DeliveryState(
        request_id="req_test",
        repo_path="/tmp/repo",
        original_request="Update README",
        test_status="failed",
        test_failure_category="attribute_error",
        test_failure_analysis_summary="AttributeError happened.",
        test_failure_likely_causes=["A field name is wrong."],
        test_failure_next_actions=["Align field names."],
        changed_files=["src/app/main.py"],
    )

    enrich_state_for_fix_patch(state)

    assert "Fix the current failed delivery workflow" in state.original_request
    assert "AttributeError happened." in state.original_request
    assert state.likely_files == ["src/app/main.py"]
