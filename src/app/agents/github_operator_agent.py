from app.agents.base import AgentDefinition


GITHUB_OPERATOR_AGENT = AgentDefinition(
    role_id="github_operator_agent",
    display_name="GitHub Operator Agent",
    prompt_name="github_operator",
    output_schema=None,
)
