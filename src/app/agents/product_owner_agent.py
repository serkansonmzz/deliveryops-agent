from app.agents.base import AgentDefinition
from app.schemas.issue_spec import IssueSpec


PRODUCT_OWNER_AGENT = AgentDefinition(
    role_id="product_owner_agent",
    display_name="Product Owner Agent",
    prompt_name="product_owner",
    output_schema=IssueSpec,
)
