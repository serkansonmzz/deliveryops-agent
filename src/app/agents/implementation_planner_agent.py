from app.agents.base import AgentDefinition
from app.schemas.implementation_plan import ImplementationPlan


IMPLEMENTATION_PLANNER_AGENT = AgentDefinition(
    role_id="implementation_planner_agent",
    display_name="Implementation Planner Agent",
    prompt_name="implementation_planner",
    output_schema=ImplementationPlan,
)
