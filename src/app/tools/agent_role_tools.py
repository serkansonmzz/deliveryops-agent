from app.agents.role_registry import get_agent_role_spec, get_agent_role_specs
from app.schemas.agent_role import AgentRoleSpec, AgentRoleStatus


def list_agent_roles() -> list[AgentRoleSpec]:
    return list(get_agent_role_specs().values())


def determine_role_status(role: AgentRoleSpec) -> str:
    if role.implemented_capabilities and not role.future_capabilities:
        return "implemented"

    if role.implemented_capabilities and role.future_capabilities:
        return "partially_implemented"

    return "planned"


def summarize_agent_role_status(role_id: str) -> AgentRoleStatus:
    role = get_agent_role_spec(role_id)
    status = determine_role_status(role)

    summary = (
        f"{role.display_name} is `{status}`. "
        f"Implemented capabilities: {len(role.implemented_capabilities)}. "
        f"Future capabilities: {len(role.future_capabilities)}."
    )

    notes: list[str] = []

    if status == "partially_implemented":
        notes.append("This role has working MVP capabilities but is not fully formalized as a dedicated Agno agent yet.")

    if role.future_capabilities:
        notes.append("Future capabilities should be implemented in later hardening phases.")

    return AgentRoleStatus(
        role_id=role.role_id,
        display_name=role.display_name,
        status=status,
        summary=summary,
        implemented_capabilities=role.implemented_capabilities,
        future_capabilities=role.future_capabilities,
        notes=notes,
    )
