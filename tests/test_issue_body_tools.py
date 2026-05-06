from app.schemas.feature_request import FeatureRequest
from app.schemas.issue_spec import IssueSpec
from app.tools.issue_body_tools import (
    build_issue_title,
    build_issue_body,
    build_issue_body_from_feature_request,
    build_issue_spec,
    ensure_issue_spec_has_body,
)


def test_build_issue_title_short_request():
    title = build_issue_title("Add a healthcheck endpoint")

    assert title == "Add a healthcheck endpoint"


def test_build_issue_title_long_request_is_truncated():
    request = "x" * 120

    title = build_issue_title(request)

    assert len(title) <= 80
    assert title.endswith("...")


def test_build_issue_body_contains_request():
    body = build_issue_body("Add a healthcheck endpoint")

    assert "# DeliveryOps Feature Request" in body
    assert "Add a healthcheck endpoint" in body
    assert "Acceptance Criteria" in body
    assert "Definition of Done" in body


def test_build_issue_spec():
    spec = build_issue_spec("Add a healthcheck endpoint")

    assert spec.title == "Add a healthcheck endpoint"
    assert "Add a healthcheck endpoint" in spec.body
    assert spec.labels == ["deliveryops"]


def test_build_issue_body_from_feature_request_includes_core_sections():
    feature_request = FeatureRequest(
        title="Add healthcheck",
        summary="Add a healthcheck endpoint.",
        problem="No healthcheck exists.",
        goal="Expose a basic healthcheck.",
        constraints=["Keep it minimal."],
        assumptions=["FastAPI project."],
        initial_risks=["Route naming may conflict."],
    )

    body = build_issue_body_from_feature_request(feature_request)

    assert "## Problem" in body
    assert "No healthcheck exists." in body
    assert "## Goal" in body
    assert "Expose a basic healthcheck." in body
    assert "- Keep it minimal." in body


def test_ensure_issue_spec_has_body_builds_body_when_empty():
    issue_spec = IssueSpec(
        title="Add healthcheck",
        body="",
        acceptance_criteria=["Healthcheck endpoint returns success."],
        definition_of_done=["Tests pass."],
        technical_notes=["Keep change minimal."],
        risk_notes=["No major risk."],
    )

    updated = ensure_issue_spec_has_body(issue_spec)

    assert updated.body
    assert "Acceptance Criteria" in updated.body
    assert "Healthcheck endpoint returns success." in updated.body
