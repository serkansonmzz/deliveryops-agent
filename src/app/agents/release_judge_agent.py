from app.agents.base import AgentDefinition
from app.schemas.release_readiness import ReleaseReadinessResult


RELEASE_JUDGE_AGENT = AgentDefinition(
    role_id="release_judge_agent",
    display_name="Release Judge Agent",
    prompt_name="release_judge",
    output_schema=ReleaseReadinessResult,
)
