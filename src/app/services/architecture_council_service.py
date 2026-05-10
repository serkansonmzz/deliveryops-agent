import os
import time
from pathlib import Path

from agno.agent import Agent

from app.agents.agent_definitions import get_agent_definition
from app.agents.factory import build_agno_agent
from app.schemas.architecture_review import ArchitectureReview
from app.schemas.delivery_state import DeliveryState
from app.services.service_result import ServiceResult
from app.state_store import load_state, save_state
from app.tools.architecture_review_tools import (
    apply_architecture_review_to_state,
    build_fallback_architecture_review,
)
from app.tools.agent_runtime_tools import (
    append_agent_timing_log,
    resolve_agent_model,
    run_agent_with_timeout,
)
from app.tools.markdown_tracking_tools import update_delivery_markdown


def can_use_llm() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def build_architecture_council_prompt(state: DeliveryState) -> str:
    likely_files = "\n".join(f"- {file_path}" for file_path in state.likely_files) or "- none"
    risky_files = "\n".join(f"- {file_path}" for file_path in state.repo_risky_files) or "- none"
    detected_stack = ", ".join(state.detected_stack) or "unknown"

    source_test_map_lines: list[str] = []
    for source_file, test_files in list(state.repo_source_test_map.items())[:20]:
        source_test_map_lines.append(f"- {source_file}")
        for test_file in test_files:
            source_test_map_lines.append(f"  - {test_file}")
    source_test_map = "\n".join(source_test_map_lines) or "- none"

    return "\n".join(
        [
            "Perform a lightweight architecture review for this delivery request.",
            "",
            "Original request:",
            state.original_request,
            "",
            f"Feature title: {state.feature_request_title or 'not available'}",
            f"Issue title: {state.issue_spec_title or 'not available'}",
            "",
            f"Detected stack: {detected_stack}",
            "",
            "Repository analysis summary:",
            state.repo_analysis_summary or "not available",
            "",
            "Likely affected files:",
            likely_files,
            "",
            "Risky files:",
            risky_files,
            "",
            "Source/test map:",
            source_test_map,
            "",
            "Policy profile:",
            getattr(state, "policy_profile", None) or "not set",
            "",
            "Return a structured ArchitectureReview.",
            "Keep the review practical and implementation-oriented.",
            "Do not recommend broad refactors unless clearly necessary.",
            "Do not suggest modifying secrets or environment files.",
        ]
    )


def build_architecture_review_for_state(
    state: DeliveryState,
    use_llm: bool | None = None,
) -> ArchitectureReview:
    should_use_llm = can_use_llm() if use_llm is None else use_llm

    if not should_use_llm:
        return build_fallback_architecture_review(state)

    try:
        definition = get_agent_definition("architecture_council_agent")
        agent: Agent = build_agno_agent(definition)
        started_at = time.monotonic()
        response = run_agent_with_timeout(agent, build_architecture_council_prompt(state))
        append_agent_timing_log(
            Path(state.repo_path),
            agent_name="architecture_council_agent",
            model=resolve_agent_model(definition),
            duration_seconds=time.monotonic() - started_at,
            status="completed",
        )
        content = response.content

        if isinstance(content, ArchitectureReview):
            return content

        if isinstance(content, dict):
            return ArchitectureReview.model_validate(content)

        return build_fallback_architecture_review(state)
    except Exception:
        return build_fallback_architecture_review(state)


def run_architecture_council_agent(
    repo_path: Path,
    use_llm: bool | None = None,
) -> ServiceResult:
    state = load_state(repo_path)
    review = build_architecture_review_for_state(state, use_llm=use_llm)
    apply_architecture_review_to_state(state, review)
    save_state(state)
    update_delivery_markdown(state)

    return ServiceResult(
        status="reviewed",
        message=review.summary,
        details={
            "source": review.source,
            "confidence_score": review.confidence_score,
            "affected_areas": len(review.affected_areas),
            "risks": len(review.risks),
            "security_notes": len(review.security_notes),
            "testing_notes": len(review.testing_notes),
        },
        warnings=review.risks,
    )
