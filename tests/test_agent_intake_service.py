from app.schemas.feature_request import FeatureRequest
from app.services.agent_intake_service import run_intake_agent


def test_run_intake_agent_falls_back_without_llm():
    result = run_intake_agent(
        raw_request="Add a healthcheck endpoint.",
        repo_path=".",
        use_llm=False,
    )

    assert isinstance(result, FeatureRequest)
    assert result.title == "Add a healthcheck endpoint."
    assert result.goal == "Add a healthcheck endpoint."
    assert result.assumptions


def test_run_intake_agent_handles_empty_request_without_llm():
    result = run_intake_agent(
        raw_request="",
        repo_path=".",
        use_llm=False,
    )

    assert result.title == "Untitled delivery request"
    assert result.summary == "Untitled delivery request"


def test_feature_request_title_is_trimmed_to_80_chars():
    raw = "A" * 120

    result = FeatureRequest.from_raw_request(raw)

    assert len(result.title) == 80
