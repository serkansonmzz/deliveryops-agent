import pytest

from app.schemas.delivery_state import DeliveryState
from app.tools.policy_profile_tools import (
    validate_policy_profile,
    normalize_policy_profile,
    evaluate_policy_action,
    ensure_policy_allows_action,
    get_safe_auto_actions_for_profile,
)


def test_validate_policy_profile_accepts_known_profile():
    assert validate_policy_profile("sandbox") == "sandbox"
    assert validate_policy_profile("personal_repo") == "personal_repo"
    assert validate_policy_profile("production_repo") == "production_repo"


def test_validate_policy_profile_rejects_unknown_profile():
    with pytest.raises(RuntimeError):
        validate_policy_profile("chaos_mode")


def test_normalize_policy_profile_defaults_to_personal_repo():
    assert normalize_policy_profile("unknown") == "personal_repo"
    assert normalize_policy_profile(None) == "personal_repo"


def test_personal_repo_requires_approval_for_git_push():
    state = DeliveryState(
        request_id="req_test",
        repo_path="/tmp/repo",
        original_request="Add policy profiles",
        policy_profile="personal_repo",
    )

    decision = evaluate_policy_action(state, "git_push")

    assert decision.permission == "approval_required"


def test_production_blocks_push_without_readiness_and_tests():
    state = DeliveryState(
        request_id="req_test",
        repo_path="/tmp/repo",
        original_request="Add policy profiles",
        policy_profile="production_repo",
        readiness_status="needs_review",
        test_status="not_detected",
    )

    decision = evaluate_policy_action(state, "git_push")

    assert decision.permission == "blocked"
    assert decision.blockers


def test_production_allows_push_after_readiness_and_tests():
    state = DeliveryState(
        request_id="req_test",
        repo_path="/tmp/repo",
        original_request="Add policy profiles",
        policy_profile="production_repo",
        readiness_status="ready",
        test_status="passed",
    )

    decision = evaluate_policy_action(state, "git_push")

    assert decision.permission == "approval_required"


def test_blocked_action_raises():
    state = DeliveryState(
        request_id="req_test",
        repo_path="/tmp/repo",
        original_request="Add policy profiles",
        policy_profile="personal_repo",
    )

    with pytest.raises(RuntimeError):
        ensure_policy_allows_action(state, "force_push")


def test_safe_auto_actions_depend_on_profile():
    sandbox_actions = get_safe_auto_actions_for_profile("sandbox")
    production_actions = get_safe_auto_actions_for_profile("production_repo")

    assert "generate_commit_message" in sandbox_actions
    assert "final_report" in production_actions
