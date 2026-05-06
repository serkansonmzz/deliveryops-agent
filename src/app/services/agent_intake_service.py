import os

from agno.agent import Agent

from app.agents.agent_definitions import get_agent_definition
from app.agents.factory import build_agno_agent
from app.schemas.feature_request import FeatureRequest


def can_use_llm() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def build_intake_prompt(raw_request: str, repo_path: str | None = None) -> str:
    return "\n".join(
        [
            "Convert this raw user request into a structured FeatureRequest.",
            "",
            f"Repository path: {repo_path or 'not provided'}",
            "",
            "Raw request:",
            raw_request,
        ]
    )


def run_intake_agent(
    raw_request: str,
    repo_path: str | None = None,
    use_llm: bool | None = None,
) -> FeatureRequest:
    should_use_llm = can_use_llm() if use_llm is None else use_llm

    if not should_use_llm:
        return FeatureRequest.from_raw_request(raw_request)

    try:
        definition = get_agent_definition("intake_agent")
        agent: Agent = build_agno_agent(definition)
        response = agent.run(build_intake_prompt(raw_request, repo_path))
        content = response.content

        if isinstance(content, FeatureRequest):
            return content

        if isinstance(content, dict):
            return FeatureRequest.model_validate(content)

        return FeatureRequest.from_raw_request(raw_request)
    except Exception:
        return FeatureRequest.from_raw_request(raw_request)
