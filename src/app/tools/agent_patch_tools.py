import os
from pathlib import Path
from dotenv import load_dotenv
from agno.agent import Agent

from app.schemas.agent_patch_response import AgentPatchResponse
from app.schemas.delivery_state import DeliveryState
from app.state_store import save_state
from app.tools.diff_tools import write_generated_patch
from app.tools.repo_context_tools import collect_repo_context
from app.tools.patch_sanitizer_tools import sanitize_agent_patch_output
from app.tools.patch_validator_tools import (
    validate_unified_diff_or_raise,
    validate_patch_can_apply_or_raise,
)

MAX_DEV_PATCH_ATTEMPTS = 3

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
- Hunk headers must use numeric line counts only, for example @@ -0,0 +1,12 @@.
- Never write words such as "thirty" inside hunk headers.
- Prefer updating existing files over creating many new files.
- If there is not enough context, produce an empty but valid response explanation instead of hallucinating.
"""


def build_agent_patch_prompt(context: dict) -> str:
    dev_patch_context = context.get("dev_patch_context")
    if dev_patch_context:
        return f"""
Generate a minimal unified diff patch using the following DevPatchContext.

{dev_patch_context}

Important:
- Follow the patch rules exactly.
- Only modify files that are relevant to the implementation plan.
- Do not modify blocked files, secrets, credentials, or environment files.
- Do not invent files unless the implementation plan clearly requires it.
- If there is not enough context, return an empty unified_diff and explain why in rationale.
"""

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


def build_retry_patch_prompt(context: dict, validation_error: str, attempt: int) -> str:
    return (
        build_agent_patch_prompt(context)
        + "\n\nPrevious patch attempt was rejected by validation.\n"
        + f"Attempt: {attempt}\n"
        + "Validation error:\n"
        + validation_error
        + "\n\nRetry requirements:\n"
        + "- Return a complete unified diff only in unified_diff.\n"
        + "- Include diff headers, file headers, and hunk headers for every file.\n"
        + "- Hunk header line counts must be numeric and accurate.\n"
        + "- Do not include prose, markdown fences, or abbreviated patches.\n"
    )


def _write_agent_raw_output(repo_path: Path, content: object, attempt: int) -> None:
    debug_dir = repo_path / ".deliveryops"
    debug_dir.mkdir(exist_ok=True)
    (debug_dir / "agent_raw_output.txt").write_text(str(content), encoding="utf-8")
    (debug_dir / f"agent_raw_output_attempt_{attempt}.txt").write_text(
        str(content),
        encoding="utf-8",
    )


def _validate_agent_patch(repo_path: Path, patch_text: str) -> None:
    validate_unified_diff_or_raise(patch_text)
    validate_patch_can_apply_or_raise(repo_path, patch_text)


def generate_patch_with_agent(repo_path: Path, state: DeliveryState) -> Path | None:
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set.")

    context = collect_repo_context(repo_path, state)
    save_state(state)

    agent = Agent(
        model="openai:gpt-5",
        instructions=DEV_AGENT_INSTRUCTIONS,
        output_schema=AgentPatchResponse,
        structured_outputs=True,
        markdown=False,
    )

    generated_patch_path = repo_path / ".deliveryops" / "generated.patch"
    if generated_patch_path.exists():
        generated_patch_path.unlink()

    prompt = build_agent_patch_prompt(context)
    last_error = ""

    for attempt in range(1, MAX_DEV_PATCH_ATTEMPTS + 1):
        response = agent.run(prompt)
        content = response.content
        _write_agent_raw_output(repo_path, content, attempt)
        patch_text = ""

        try:
            if not content or not content.unified_diff.strip():
                raise RuntimeError("Agent output did not contain a usable unified diff patch.")

            patch_text = sanitize_agent_patch_output(content.unified_diff)

            if not patch_text:
                raise RuntimeError("Agent output did not contain a usable unified diff patch.")

            _validate_agent_patch(repo_path, patch_text)
            state.dev_context_status = "patch_generated"
            state.last_error = None
            return write_generated_patch(repo_path, patch_text)
        except RuntimeError as exc:
            last_error = str(exc)
            workspace = repo_path / ".deliveryops"
            workspace.mkdir(exist_ok=True)
            if patch_text:
                (workspace / "rejected.patch").write_text(patch_text, encoding="utf-8")
            (workspace / "patch_validation_error.txt").write_text(
                last_error,
                encoding="utf-8",
            )
            state.dev_context_status = "patch_generation_retrying"
            save_state(state)

            if attempt == MAX_DEV_PATCH_ATTEMPTS:
                break

            prompt = build_retry_patch_prompt(context, last_error, attempt + 1)

    state.dev_context_status = "patch_generation_failed"
    state.patch_summary = (
        "Dev Agent produced a patch, but it was rejected by validation. "
        "No patch was applied."
    )
    state.last_error = last_error
    save_state(state)
    raise RuntimeError(
        "Dev Agent patch generation failed after validation retries. "
        "No patch was applied. See `.deliveryops/rejected.patch`, "
        "`.deliveryops/patch_validation_error.txt`, and agent raw output files."
    )
