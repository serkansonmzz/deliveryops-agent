import os

from agno.agent import Agent

from app.agents.agent_definitions import get_agent_definition
from app.agents.factory import build_agno_agent
from app.schemas.feature_request import FeatureRequest
from app.schemas.issue_spec import IssueSpec
from app.tools.issue_body_tools import ensure_issue_spec_has_body


def can_use_llm() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def build_product_owner_prompt(feature_request: FeatureRequest) -> str:
    return "\n".join(
        [
            "Create a high-quality GitHub issue specification from this FeatureRequest.",
            "",
            f"Title: {feature_request.title}",
            f"Summary: {feature_request.summary}",
            f"Problem: {feature_request.problem or 'not provided'}",
            f"Goal: {feature_request.goal}",
            "",
            "Constraints:",
            "\n".join(f"- {item}" for item in feature_request.constraints) or "- none",
            "",
            "Assumptions:",
            "\n".join(f"- {item}" for item in feature_request.assumptions) or "- none",
            "",
            "Initial risks:",
            "\n".join(f"- {item}" for item in feature_request.initial_risks) or "- none",
        ]
    )


def build_fallback_issue_spec(feature_request: FeatureRequest) -> IssueSpec:
    issue_spec = IssueSpec.from_feature_request(
        request_title=feature_request.title,
        request_summary=feature_request.summary,
    )
    return ensure_issue_spec_has_body(issue_spec)


def run_product_owner_agent(
    feature_request: FeatureRequest,
    use_llm: bool | None = None,
) -> IssueSpec:
    should_use_llm = can_use_llm() if use_llm is None else use_llm

    if not should_use_llm:
        return build_fallback_issue_spec(feature_request)

    try:
        definition = get_agent_definition("product_owner_agent")
        agent: Agent = build_agno_agent(definition)
        response = agent.run(build_product_owner_prompt(feature_request))
        content = response.content

        if isinstance(content, IssueSpec):
            return ensure_issue_spec_has_body(content)

        if isinstance(content, dict):
            return ensure_issue_spec_has_body(IssueSpec.model_validate(content))

        return build_fallback_issue_spec(feature_request)
    except Exception:
        return build_fallback_issue_spec(feature_request)
