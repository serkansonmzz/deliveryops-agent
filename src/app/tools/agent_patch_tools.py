import os
import time
from collections.abc import Callable
from pathlib import Path
from dotenv import load_dotenv
from agno.agent import Agent

from app.schemas.agent_patch_response import AgentPatchResponse
from app.schemas.delivery_state import DeliveryState
from app.state_store import save_state
from app.tools.agent_runtime_tools import (
    append_agent_timing_log,
    get_agent_timeout_seconds,
    run_agent_with_timeout,
)
from app.tools.deterministic_patch_builder_tools import build_patch_from_file_edits
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
- Prefer producing structured file_edits. DeliveryOps will build the unified diff.
- Use unified_diff only as a fallback when file_edits cannot express the change.
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
- Prefer file_edits over unified_diff.
- Use edit_type values only from: create_file, replace_text, append_after, append_to_file.
- For replace_text and append_after, provide an exact anchor from the selected file content.
- For create_file, provide the full file content.
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
        + "- Prefer corrected file_edits if the change can be expressed structurally.\n"
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


def _extract_patch_text(repo_path: Path, content: AgentPatchResponse) -> tuple[str, str]:
    if content.file_edits:
        return build_patch_from_file_edits(repo_path, content.file_edits), "file_edits"

    if content.unified_diff.strip():
        return sanitize_agent_patch_output(content.unified_diff), "unified_diff"

    raise RuntimeError("Agent output did not contain file_edits or a usable unified diff patch.")


def _record_patch_attempt(
    state: DeliveryState,
    *,
    attempt: int,
    mode: str,
    status: str,
    elapsed_seconds: float,
    error: str | None = None,
) -> None:
    entry = {
        "attempt": attempt,
        "mode": mode,
        "status": status,
        "elapsed_seconds": round(elapsed_seconds, 3),
    }
    if error:
        entry["error"] = error
    state.patch_generation_attempts.append(entry)


def generate_patch_with_agent(
    repo_path: Path,
    state: DeliveryState,
    progress: Callable[[str], None] | None = None,
) -> Path | None:
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set.")

    context = collect_repo_context(repo_path, state)
    save_state(state)

    model = os.getenv("DELIVERYOPS_DEV_MODEL") or "openai:gpt-5"
    agent = Agent(
        model=model,
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
    state.patch_generation_attempts = []
    state.patch_generation_blocked_reason = None

    for attempt in range(1, MAX_DEV_PATCH_ATTEMPTS + 1):
        if progress:
            progress(f"Attempt {attempt}/{MAX_DEV_PATCH_ATTEMPTS} started.")

        started_at = time.monotonic()
        patch_text = ""
        generation_mode = "unknown"

        try:
            response = run_agent_with_timeout(
                agent,
                prompt,
                timeout_seconds=get_agent_timeout_seconds(),
            )
            elapsed = time.monotonic() - started_at
            content = response.content
            _write_agent_raw_output(repo_path, content, attempt)

            if not content:
                raise RuntimeError("Agent output was empty.")

            patch_text, generation_mode = _extract_patch_text(repo_path, content)
            if not patch_text:
                raise RuntimeError("Agent output did not produce patch content.")

            _validate_agent_patch(repo_path, patch_text)
            _record_patch_attempt(
                state,
                attempt=attempt,
                mode=generation_mode,
                status="accepted",
                elapsed_seconds=elapsed,
            )
            append_agent_timing_log(
                repo_path,
                agent_name="dev_agent",
                model=model,
                duration_seconds=elapsed,
                status="accepted",
                attempt=attempt,
            )
            state.dev_context_status = "patch_generated"
            state.patch_generation_blocked_reason = None
            state.last_error = None
            if progress:
                progress(
                    f"Attempt {attempt}/{MAX_DEV_PATCH_ATTEMPTS} accepted "
                    f"using {generation_mode}."
                )
            return write_generated_patch(repo_path, patch_text)
        except (RuntimeError, TimeoutError) as exc:
            last_error = str(exc)
            elapsed = time.monotonic() - started_at
            workspace = repo_path / ".deliveryops"
            workspace.mkdir(exist_ok=True)
            if patch_text:
                (workspace / "rejected.patch").write_text(patch_text, encoding="utf-8")
            (workspace / "patch_validation_error.txt").write_text(
                last_error,
                encoding="utf-8",
            )
            _record_patch_attempt(
                state,
                attempt=attempt,
                mode=generation_mode,
                status="rejected",
                elapsed_seconds=elapsed,
                error=last_error,
            )
            append_agent_timing_log(
                repo_path,
                agent_name="dev_agent",
                model=model,
                duration_seconds=elapsed,
                status="rejected",
                attempt=attempt,
                error=last_error,
            )
            state.dev_context_status = "patch_generation_retrying"
            save_state(state)
            if progress:
                progress(
                    f"Attempt {attempt}/{MAX_DEV_PATCH_ATTEMPTS} validation failed; "
                    "retrying with validation error."
                )

            if attempt == MAX_DEV_PATCH_ATTEMPTS:
                break

            prompt = build_retry_patch_prompt(context, last_error, attempt + 1)

    state.dev_context_status = "patch_generation_failed"
    state.patch_generation_blocked_reason = "blocked_by_invalid_patch"
    if state.pending_action == "apply_patch":
        state.pending_action = None
        state.pending_approval = False
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
