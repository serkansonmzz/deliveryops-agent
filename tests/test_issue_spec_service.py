from app.schemas.feature_request import FeatureRequest
from app.schemas.issue_spec import IssueSpec
from app.services.issue_spec_service import (
    build_fallback_issue_spec,
    run_product_owner_agent,
)


def test_build_fallback_issue_spec_contains_required_sections():
    feature_request = FeatureRequest(
        title="Add healthcheck",
        summary="Add a healthcheck endpoint.",
        goal="Expose a healthcheck endpoint.",
    )

    issue_spec = build_fallback_issue_spec(feature_request)

    assert isinstance(issue_spec, IssueSpec)
    assert issue_spec.title == "Add healthcheck"
    assert "## Problem" in issue_spec.body
    assert "## Acceptance Criteria" in issue_spec.body
    assert issue_spec.acceptance_criteria


def test_run_product_owner_agent_falls_back_without_llm():
    feature_request = FeatureRequest(
        title="Add healthcheck",
        summary="Add a healthcheck endpoint.",
        goal="Expose a healthcheck endpoint.",
    )

    issue_spec = run_product_owner_agent(feature_request, use_llm=False)

    assert issue_spec.title == "Add healthcheck"
    assert issue_spec.body
    assert "Definition of Done" in issue_spec.body
