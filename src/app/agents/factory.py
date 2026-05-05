from agno.agent import Agent

from app.agents.base import AgentDefinition
from app.tools.prompt_tools import load_prompt


def build_agno_agent(definition: AgentDefinition) -> Agent:
    instructions = load_prompt(definition.prompt_name)

    kwargs = {
        "model": definition.model,
        "instructions": instructions,
        "markdown": False,
    }

    if definition.output_schema is not None:
        kwargs["output_schema"] = definition.output_schema
        kwargs["structured_outputs"] = True

    return Agent(**kwargs)
