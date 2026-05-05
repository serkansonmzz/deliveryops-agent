from app.agents.base import AgentDefinition
from app.schemas.feature_request import FeatureRequest


INTAKE_AGENT = AgentDefinition(
    role_id="intake_agent",
    display_name="Intake Agent",
    prompt_name="intake",
    output_schema=FeatureRequest,
)
