from pathlib import Path

from app.schemas.delivery_state import DeliveryState
from app.tools.architecture_review_tools import (
    apply_architecture_review_to_state,
    build_architecture_review,
    build_fallback_architecture_review,
    build_implementation_plan,
)


def test_build_architecture_review_for_github_request(tmp_path: Path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='test'\n")

    review = build_architecture_review(
        tmp_path,
        "Add GitHub issue creation to delivery run",
    )

    assert "python" in review.detected_stack
    assert "GitHub workflow integration" in review.affected_areas
    assert review.summary


def test_build_implementation_plan_has_steps(tmp_path: Path):
    review = build_architecture_review(
        tmp_path,
        "Add branch creation to delivery run",
    )

    plan = build_implementation_plan(review)

    assert len(plan.steps) >= 5
    assert any("branch" in step.lower() for step in plan.steps)


def test_build_fallback_architecture_review_uses_state_context():
    state = DeliveryState(
        request_id="req_test",
        repo_path="/tmp/repo",
        original_request="Update README docs",
        detected_stack=["python", "uv"],
        likely_files=["README.md"],
        repo_risky_files=[".github/workflows/ci.yml"],
    )

    review = build_fallback_architecture_review(state)

    assert review.source == "fallback"
    assert "README.md" in review.affected_areas
    assert review.confidence_score < 0.6
    assert review.risks


def test_apply_architecture_review_to_state():
    state = DeliveryState(
        request_id="req_test",
        repo_path="/tmp/repo",
        original_request="Update README docs",
    )
    review = build_fallback_architecture_review(state)

    apply_architecture_review_to_state(state, review)

    assert state.architecture_review_summary
    assert state.architecture_review_source == "fallback"
    assert state.architecture_confidence_score == review.confidence_score
    assert "architecture_review" in state.completed_steps
    assert "run_architecture_review" in state.completed_steps
