import pytest

from app.agents.agent_definitions import (
    get_agent_definition,
    get_agent_definitions,
)
from app.agents.base import describe_agent


EXPECTED_AGENTS = {
    "intake_agent",
    "product_owner_agent",
    "architecture_council_agent",
    "implementation_planner_agent",
    "delivery_manager_agent",
    "github_operator_agent",
    "dev_agent",
    "test_agent",
    "release_judge_agent",
}


def test_agent_definitions_include_expected_agents():
    agents = get_agent_definitions()

    assert EXPECTED_AGENTS.issubset(set(agents.keys()))


def test_get_agent_definition_rejects_unknown_agent():
    with pytest.raises(RuntimeError):
        get_agent_definition("chaos_agent")


def test_dev_agent_definition_has_patch_schema():
    definition = get_agent_definition("dev_agent")

    assert definition.role_id == "dev_agent"
    assert definition.output_schema is not None
    assert "patch" in definition.output_schema.__name__.lower()


def test_architecture_council_agent_has_review_schema():
    definition = get_agent_definition("architecture_council_agent")

    assert definition.role_id == "architecture_council_agent"
    assert definition.output_schema is not None
    assert "ArchitectureReview" in definition.output_schema.__name__


def test_implementation_planner_agent_has_plan_schema():
    definition = get_agent_definition("implementation_planner_agent")

    assert definition.role_id == "implementation_planner_agent"
    assert definition.output_schema is not None
    assert "ImplementationPlan" in definition.output_schema.__name__


def test_describe_agent_mentions_prompt_and_schema():
    definition = get_agent_definition("intake_agent")

    description = describe_agent(definition)

    assert "Intake Agent" in description
    assert "intake" in description
    assert "FeatureRequest" in description
