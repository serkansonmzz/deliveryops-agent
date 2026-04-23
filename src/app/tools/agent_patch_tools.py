import os
from pathlib import Path
from dotenv import load_dotenv
from agno.agent import Agent

from app.schemas.agent_patch_response import AgentPatchResponse
from app.schemas.delivery_state import DeliveryState
from app.tools.diff_tools import write_generated_patch
from app.tools.repo_context_tools import collect_repo_context
from app.tools.patch_sanitizer_tools import sanitize_agent_patch_output
from app.tools.patch_validator_tools import (
    validate_unified_diff_or_raise,
    validate_patch_can_apply_or_raise,
)

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

    debug_path = repo_path / ".deliveryops" / "agent_raw_output.txt"
    debug_path.parent.mkdir(exist_ok=True)
    debug_path.write_text(str(content), encoding="utf-8")

    if not content or not content.unified_diff.strip():
        raise RuntimeError("Agent output did not contain a usable unified diff patch.") 

    patch_text = sanitize_agent_patch_output(content.unified_diff)

    if not patch_text:
        raise RuntimeError("Agent output did not contain a usable unified diff patch.")

    generated_patch_path = repo_path / ".deliveryops" / "generated.patch"
    if generated_patch_path.exists():
        generated_patch_path.unlink()

    validate_unified_diff_or_raise(patch_text)
    validate_patch_can_apply_or_raise(repo_path, patch_text)

    return write_generated_patch(repo_path, patch_text)