import os
from pathlib import Path

from agno.agent import Agent

from app.agents.agent_definitions import get_agent_definition
from app.agents.factory import build_agno_agent
from app.schemas.delivery_state import DeliveryState
from app.schemas.implementation_plan import ImplementationPlan
from app.services.service_result import ServiceResult
from app.state_store import load_state, save_state
from app.tools.implementation_plan_tools import (
    apply_implementation_plan_to_state,
    build_fallback_implementation_plan,
)
from app.tools.markdown_tracking_tools import update_delivery_markdown


def can_use_llm() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def build_implementation_plan_prompt(state: DeliveryState) -> str:
    likely_files = "\n".join(f"- {file_path}" for file_path in state.likely_files) or "- none"
    affected_areas = "\n".join(f"- {item}" for item in state.affected_areas) or "- none"
    recommended_approach = "\n".join(
        f"- {item}" for item in state.architecture_recommended_approach
    ) or "- none"
    risks = "\n".join(f"- {item}" for item in state.risk_notes) or "- none"
    security_notes = "\n".join(f"- {item}" for item in state.security_notes) or "- none"
    testing_notes = "\n".join(f"- {item}" for item in state.testing_notes) or "- none"
    devops_notes = "\n".join(f"- {item}" for item in state.devops_notes) or "- none"
    open_questions = "\n".join(
        f"- {item}" for item in state.architecture_open_questions
    ) or "- none"

    source_test_map_lines: list[str] = []
    for source_file, test_files in list(state.repo_source_test_map.items())[:20]:
        source_test_map_lines.append(f"- {source_file}")
        for test_file in test_files:
            source_test_map_lines.append(f"  - {test_file}")
    source_test_map = "\n".join(source_test_map_lines) or "- none"

    return "\n".join(
        [
            "Create a practical implementation plan for this DeliveryOps workflow.",
            "",
            "Original request:",
            state.original_request,
            "",
            f"Feature title: {state.feature_request_title or 'not available'}",
            f"Issue title: {state.issue_spec_title or 'not available'}",
            "",
            "Repository analysis summary:",
            state.repo_analysis_summary or "not available",
            "",
            "Likely files:",
            likely_files,
            "",
            "Affected areas:",
            affected_areas,
            "",
            "Architecture review summary:",
            state.architecture_review_summary or "not available",
            "",
            "Recommended approach:",
            recommended_approach,
            "",
            "Architecture risks:",
            risks,
            "",
            "Security notes:",
            security_notes,
            "",
            "Testing notes:",
            testing_notes,
            "",
            "DevOps notes:",
            devops_notes,
            "",
            "Open questions:",
            open_questions,
            "",
            "Source/test map:",
            source_test_map,
            "",
            "Rules:",
            "- Keep steps small and reviewable.",
            "- Do not invent files.",
            "- Prefer likely files and existing files.",
            "- Include test impact for each step.",
            "- Include rollback notes for each step.",
            "- The plan must help Dev Agent generate a minimal patch later.",
        ]
    )


def build_implementation_plan_for_state(
    state: DeliveryState,
    use_llm: bool | None = None,
) -> ImplementationPlan:
    should_use_llm = can_use_llm() if use_llm is None else use_llm

    if not should_use_llm:
        return build_fallback_implementation_plan(state)

    try:
        definition = get_agent_definition("implementation_planner_agent")
        agent: Agent = build_agno_agent(definition)
        response = agent.run(build_implementation_plan_prompt(state))
        content = response.content

        if isinstance(content, ImplementationPlan):
            return content

        if isinstance(content, dict):
            return ImplementationPlan.model_validate(content)

        return build_fallback_implementation_plan(state)
    except Exception:
        return build_fallback_implementation_plan(state)


def run_implementation_planner_agent(
    repo_path: Path,
    use_llm: bool | None = None,
) -> ServiceResult:
    state = load_state(repo_path)
    plan = build_implementation_plan_for_state(state, use_llm=use_llm)
    apply_implementation_plan_to_state(state, plan)
    save_state(state)
    update_delivery_markdown(state)

    return ServiceResult(
        status="planned",
        message=plan.summary,
        details={
            "source": plan.source,
            "confidence_score": plan.confidence_score,
            "steps": len(plan.steps),
            "target_files": len(plan.target_files),
            "risks": len(plan.risks),
        },
        warnings=plan.risks,
    )
