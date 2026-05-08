from app.schemas.delivery_state import DeliveryState
from app.tools.implementation_plan_tools import (
    apply_implementation_plan_to_state,
    build_fallback_implementation_plan,
)


def test_build_fallback_implementation_plan_uses_likely_files():
    state = DeliveryState(
        request_id="req_test",
        repo_path="/tmp/repo",
        original_request="Update README docs",
        likely_files=["README.md"],
        testing_notes=["Run pytest."],
        risk_notes=["Docs-only change."],
    )

    plan = build_fallback_implementation_plan(state)

    assert plan.source == "fallback"
    assert "README.md" in plan.target_files
    assert plan.steps
    assert plan.confidence_score < 0.6


def test_apply_implementation_plan_to_state_updates_legacy_and_structured_fields():
    state = DeliveryState(
        request_id="req_test",
        repo_path="/tmp/repo",
        original_request="Update README docs",
        likely_files=["README.md"],
    )
    plan = build_fallback_implementation_plan(state)

    apply_implementation_plan_to_state(state, plan)

    assert state.implementation_plan_summary
    assert state.implementation_plan_source == "fallback"
    assert state.implementation_plan_steps
    assert state.implementation_plan
    assert "implementation_plan" in state.completed_steps
    assert "generate_implementation_plan" in state.completed_steps
