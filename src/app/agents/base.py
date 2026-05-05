from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AgentDefinition:
    role_id: str
    display_name: str
    prompt_name: str
    output_schema: type[Any] | None = None
    model: str = "openai:gpt-5"


def describe_agent(definition: AgentDefinition) -> str:
    schema_name = (
        definition.output_schema.__name__
        if definition.output_schema is not None
        else "None"
    )

    return (
        f"{definition.display_name} "
        f"({definition.role_id}) uses prompt `{definition.prompt_name}` "
        f"with output schema `{schema_name}`."
    )
