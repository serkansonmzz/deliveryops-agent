from app.tools.issue_body_tools import (
    build_issue_title,
    build_issue_body,
    build_issue_spec,
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
    assert spec.labels == []