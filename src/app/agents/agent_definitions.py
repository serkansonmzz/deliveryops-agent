from app.agents.architecture_council_agent import ARCHITECTURE_COUNCIL_AGENT
from app.agents.base import AgentDefinition
from app.agents.delivery_manager_agent import DELIVERY_MANAGER_AGENT
from app.agents.dev_agent import DEV_AGENT
from app.agents.github_operator_agent import GITHUB_OPERATOR_AGENT
from app.agents.intake_agent import INTAKE_AGENT
from app.agents.product_owner_agent import PRODUCT_OWNER_AGENT
from app.agents.release_judge_agent import RELEASE_JUDGE_AGENT
from app.agents.test_agent import TEST_AGENT


def get_agent_definitions() -> dict[str, AgentDefinition]:
    agents = [
        INTAKE_AGENT,
        PRODUCT_OWNER_AGENT,
        ARCHITECTURE_COUNCIL_AGENT,
        DELIVERY_MANAGER_AGENT,
        GITHUB_OPERATOR_AGENT,
        DEV_AGENT,
        TEST_AGENT,
        RELEASE_JUDGE_AGENT,
    ]

    return {agent.role_id: agent for agent in agents}


def get_agent_definition(role_id: str) -> AgentDefinition:
    agents = get_agent_definitions()

    if role_id not in agents:
        allowed = ", ".join(sorted(agents.keys()))
        raise RuntimeError(f"Unknown agent definition: {role_id}. Allowed: {allowed}")

    return agents[role_id]
