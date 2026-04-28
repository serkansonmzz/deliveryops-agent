import pytest

from app.agents.role_registry import get_agent_role_spec, get_agent_role_specs
from app.tools.agent_role_tools import (
    list_agent_roles,
    summarize_agent_role_status,
)


EXPECTED_ROLES = {
    "intake_agent",
    "product_owner_agent",
    "architecture_council_agent",
    "delivery_manager_agent",
    "github_operator_agent",
    "dev_agent",
    "test_agent",
    "release_judge_agent",
}


def test_all_expected_agent_roles_are_registered():
    roles = get_agent_role_specs()

    assert EXPECTED_ROLES.issubset(set(roles.keys()))


def test_list_agent_roles_returns_specs():
    roles = list_agent_roles()

    assert len(roles) >= len(EXPECTED_ROLES)
    assert all(role.role_id for role in roles)
    assert all(role.display_name for role in roles)


def test_get_agent_role_spec_rejects_unknown_role():
    with pytest.raises(RuntimeError):
        get_agent_role_spec("chaos_agent")


def test_dev_agent_status_has_patch_capabilities():
    status = summarize_agent_role_status("dev_agent")

    assert status.role_id == "dev_agent"
    assert status.status in {"implemented", "partially_implemented"}
    assert any("patch" in item.lower() for item in status.implemented_capabilities)


def test_test_agent_status_has_test_capabilities():
    status = summarize_agent_role_status("test_agent")

    assert status.role_id == "test_agent"
    assert any("test" in item.lower() for item in status.implemented_capabilities)


def test_release_judge_status_has_readiness_capabilities():
    status = summarize_agent_role_status("release_judge_agent")

    assert status.role_id == "release_judge_agent"
    assert any("readiness" in item.lower() for item in status.implemented_capabilities)
