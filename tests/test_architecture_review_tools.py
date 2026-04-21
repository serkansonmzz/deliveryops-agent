from pathlib import Path

from app.tools.architecture_review_tools import (
    build_architecture_review,
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