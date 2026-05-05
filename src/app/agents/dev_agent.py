from app.agents.base import AgentDefinition
from app.schemas.agent_patch_response import AgentPatchResponse


DEV_AGENT = AgentDefinition(
    role_id="dev_agent",
    display_name="Dev Agent",
    prompt_name="dev_agent",
    output_schema=AgentPatchResponse,
)
