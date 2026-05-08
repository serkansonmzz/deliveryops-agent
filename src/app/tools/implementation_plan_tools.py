from app.schemas.delivery_state import DeliveryState
from app.schemas.implementation_plan import ImplementationPlan


def apply_implementation_plan_to_state(
    state: DeliveryState,
    plan: ImplementationPlan,
) -> None:
    state.implementation_plan_summary = plan.summary
    state.implementation_plan_source = plan.source
    state.implementation_plan_confidence_score = plan.confidence_score
    state.implementation_plan_target_files = plan.target_files
    state.implementation_plan_test_strategy = plan.test_strategy
    state.implementation_plan_risks = plan.risks
    state.implementation_plan_assumptions = plan.assumptions
    state.implementation_plan_steps = [step.model_dump() for step in plan.steps]

    # Preserve the legacy flat plan consumed by current Dev Agent context paths.
    state.implementation_plan = [
        f"{step.step_number}. {step.title}: {step.description}"
        for step in plan.steps
    ]

    if plan.target_files:
        state.likely_files = plan.target_files

    state.mark_completed("implementation_plan")
    state.mark_completed("generate_implementation_plan")


def build_fallback_implementation_plan(state: DeliveryState) -> ImplementationPlan:
    likely_files = state.likely_files or state.affected_areas

    return ImplementationPlan.fallback(
        request=state.original_request,
        likely_files=likely_files,
        testing_notes=state.testing_notes,
        risk_notes=state.risk_notes,
    )
