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


def test_delivery_markdown_contains_architecture_review_enrichment():
    state = DeliveryState(
        request_id="req_test",
        repo_path="/tmp/repo",
        original_request="Add healthcheck endpoint.",
        architecture_review_summary="Review summary.",
        architecture_review_source="fallback",
        architecture_confidence_score=0.45,
        architecture_recommended_approach=["Keep the change focused."],
        architecture_open_questions=["Confirm endpoint path."],
    )

    markdown = render_delivery_markdown(state)

    assert "## Architecture Review Summary" in markdown
    assert "Source: `fallback`" in markdown
    assert "Confidence Score: `0.45`" in markdown
    assert "Keep the change focused." in markdown
    assert "Confirm endpoint path." in markdown


def test_delivery_markdown_contains_structured_implementation_plan():
    state = DeliveryState(
        request_id="req_test",
        repo_path="/tmp/repo",
        original_request="Add healthcheck endpoint.",
        implementation_plan_summary="Plan summary.",
        implementation_plan_source="fallback",
        implementation_plan_confidence_score=0.45,
        implementation_plan_target_files=["README.md"],
        implementation_plan_test_strategy=["Run pytest."],
        implementation_plan_risks=["Docs-only change."],
        implementation_plan_assumptions=["Fallback planning."],
        implementation_plan_steps=[
            {
                "step_number": 1,
                "title": "Update docs",
                "description": "Update README docs.",
                "target_files": ["README.md"],
                "expected_changes": ["Add usage notes."],
                "test_impact": ["Run pytest."],
                "risk_level": "low",
            }
        ],
        implementation_plan=["1. Update docs: Update README docs."],
    )

    markdown = render_delivery_markdown(state)

    assert "## Implementation Plan" in markdown
    assert "Plan summary." in markdown
    assert "Source: `fallback`" in markdown
    assert "Confidence Score: `0.45`" in markdown
    assert "`README.md`" in markdown
    assert "#### Step 1: Update docs" in markdown
    assert "### Legacy Flat Plan" in markdown
