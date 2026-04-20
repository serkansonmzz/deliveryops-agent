from app.schemas.delivery_state import DeliveryState
from app.tools.markdown_tracking_tools import render_delivery_markdown


def test_delivery_markdown_contains_request():
    state = DeliveryState(
        request_id="req_test",
        repo_path="/tmp/repo",
        original_request="Add healthcheck endpoint.",
    )

    markdown = render_delivery_markdown(state)

    assert "# DeliveryOps Runbook" in markdown
    assert "Add healthcheck endpoint." in markdown
    assert "- [ ] Inspect repository" in markdown


def test_delivery_markdown_marks_completed_steps():
    state = DeliveryState(
        request_id="req_test",
        repo_path="/tmp/repo",
        original_request="Add healthcheck endpoint.",
        completed_steps=["inspect_repository"],
    )

    markdown = render_delivery_markdown(state)

    assert "- [x] Inspect repository" in markdown