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


def test_delivery_markdown_contains_structured_request_section():
    state = DeliveryState(
        request_id="req_test",
        repo_path="/tmp/repo",
        original_request="Add healthcheck endpoint.",
        feature_request_title="Add healthcheck endpoint",
        feature_request_summary="Add healthcheck endpoint.",
        issue_spec_title="Add healthcheck endpoint",
    )

    markdown = render_delivery_markdown(state)

    assert "## Structured Request" in markdown
    assert "Feature Title" in markdown
    assert "Issue Spec Title" in markdown


def test_delivery_markdown_contains_repository_analysis_section():
    state = DeliveryState(
        request_id="req_test",
        repo_path="/tmp/repo",
        original_request="Add healthcheck endpoint.",
        repo_analysis_summary="Repository analysis found 4 files.",
        repo_source_file_count=1,
        repo_test_file_count=1,
        repo_documentation_file_count=1,
        repo_config_file_count=1,
        repo_risky_files=[".github/workflows/ci.yml"],
        repo_source_test_map={"src/app/main.py": ["tests/test_main.py"]},
    )

    markdown = render_delivery_markdown(state)

    assert "## Repository Analysis" in markdown
    assert "Repository analysis found 4 files." in markdown
    assert "Source Files: `1`" in markdown
    assert "`src/app/main.py`" in markdown
