import os
from pathlib import Path
from dotenv import load_dotenv
from agno.agent import Agent

from app.schemas.agent_patch_response import AgentPatchResponse
from app.schemas.delivery_state import DeliveryState
from app.tools.diff_tools import write_generated_patch
from app.tools.repo_context_tools import collect_repo_context


DEV_AGENT_INSTRUCTIONS = """
You are a careful software delivery patch generator.

Your job:
- Read the delivery request and repository context.
- Produce a valid unified diff patch.
- Only modify files that are relevant to the request.
- Keep the patch as small as possible.
- Do not invent files unless clearly necessary.
- Do not include markdown fences around the diff.
- The unified_diff field must contain a real patch that can be written to a .patch file.
- Prefer updating existing files over creating many new files.
- If there is not enough context, produce an empty but valid response explanation instead of hallucinating.
"""


def build_agent_patch_prompt(context: dict) -> str:
    return f"""
Generate a unified diff patch for this request.

Request:
{context["request"]}

Issue URL:
{context["issue_url"]}

Branch:
{context["branch_name"]}

Architecture Review Summary:
{context["architecture_review_summary"]}

Implementation Plan:
{context["implementation_plan"]}

Likely Files:
{context["likely_files"]}

Repository File Context:
{context["files"]}
"""


def generate_patch_with_agent(repo_path: Path, state: DeliveryState) -> Path | None:
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set.")

    context = collect_repo_context(repo_path, state)

    agent = Agent(
        model="openai:gpt-5",
        instructions=DEV_AGENT_INSTRUCTIONS,
        output_schema=AgentPatchResponse,
        structured_outputs=True,
        markdown=False,
    )

    response = agent.run(build_agent_patch_prompt(context))

    content = response.content

    if not content or not content.unified_diff.strip():
        return None

    return write_generated_patch(repo_path, content.unified_diff)