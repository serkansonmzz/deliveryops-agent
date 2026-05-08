from pathlib import Path

from app.schemas.architecture_review import ArchitectureReview
from app.schemas.delivery_state import DeliveryState
from app.schemas.implementation_plan import ImplementationPlan, ImplementationPlanStep
from app.tools.repo_analysis_tools import detect_project_stack, find_likely_files


def build_architecture_review(repo_path: Path, request: str) -> ArchitectureReview:
    stack = detect_project_stack(repo_path)
    likely_files = find_likely_files(repo_path, request)

    affected_areas: list[str] = []
    risks: list[str] = []
    security_notes: list[str] = []
    testing_notes: list[str] = []
    devops_notes: list[str] = []

    request_lower = request.lower()

    if "github" in request_lower or "issue" in request_lower:
        affected_areas.append("GitHub workflow integration")
        risks.append("GitHub CLI behavior may differ across versions.")

    if "branch" in request_lower or "git" in request_lower:
        affected_areas.append("Git workflow automation")
        risks.append("Branch creation can change the current working branch.")

    if "cli" in request_lower or "command" in request_lower:
        affected_areas.append("CLI command handling")
        risks.append("CLI behavior should remain backward compatible.")

    if "state" in request_lower or "delivery" in request_lower:
        affected_areas.append("DeliveryOps state tracking")
        risks.append("State and human-readable tracking files must stay synchronized.")

    if "security" in request_lower or "secret" in request_lower or "env" in request_lower:
        security_notes.append("Avoid modifying secrets or environment files without explicit approval.")
    else:
        security_notes.append("No direct security-sensitive keywords detected in the request.")

    testing_notes.append("Add or update focused unit tests for the changed behavior.")
    testing_notes.append("Run the full test suite after implementation.")

    if "github-actions" in stack:
        devops_notes.append("GitHub Actions may be affected if CLI behavior changes.")
    else:
        devops_notes.append("No CI workflow detected from repository structure.")

    if not affected_areas:
        affected_areas.append("General application workflow")

    if not risks:
        risks.append("Scope may need refinement during implementation.")

    summary = (
        "This request should be implemented as a small, reviewable change. "
        "The workflow should preserve existing behavior and keep state tracking visible."
    )

    return ArchitectureReview(
        summary=summary,
        detected_stack=stack,
        affected_areas=affected_areas,
        likely_files=likely_files,
        risks=risks,
        security_notes=security_notes,
        testing_notes=testing_notes,
        devops_notes=devops_notes,
        confidence="medium",
    )


def build_implementation_plan(review: ArchitectureReview) -> ImplementationPlan:
    target_files = review.likely_files or review.affected_areas
    test_strategy = review.testing_notes or [
        "Run the relevant test command and review the output.",
    ]
    risks = review.risks or ["Scope may need refinement during implementation."]

    if "Git workflow automation" in review.affected_areas:
        risks.append("Be careful with branch-changing Git operations and preserve workflow state.")

    if "GitHub workflow integration" in review.affected_areas:
        test_strategy.append("Verify GitHub CLI commands against the installed gh version.")

    steps = [
        ImplementationPlanStep(
            step_number=1,
            title="Confirm scope and target files",
            description=(
                "Review the generated GitHub issue, architecture review, and likely "
                "affected files before patch generation."
            ),
            target_files=target_files[:10],
            expected_changes=[
                "Confirm the smallest file set required for the requested change.",
            ],
            test_impact=["No direct test impact."],
            risk_level="low",
            acceptance_mapping=[
                "Implementation scope is understood before patch generation.",
            ],
            rollback_notes=["No code changes should be made in this step."],
        ),
        ImplementationPlanStep(
            step_number=2,
            title="Implement focused change",
            description="Make the smallest code or documentation change that satisfies the request.",
            target_files=target_files[:10],
            expected_changes=[
                "Update existing files relevant to the architecture review.",
                "Avoid unrelated refactors.",
            ],
            test_impact=test_strategy,
            risk_level="medium" if risks else "low",
            acceptance_mapping=[
                "Requested behavior is implemented or clearly documented.",
            ],
            rollback_notes=["Revert the generated patch if review or tests fail."],
        ),
        ImplementationPlanStep(
            step_number=3,
            title="Validate and prepare delivery",
            description="Run safe validation and review DeliveryOps tracking before commit, push, or PR.",
            target_files=[],
            expected_changes=[
                "No additional changes unless validation identifies a failure.",
            ],
            test_impact=test_strategy,
            risk_level="low",
            acceptance_mapping=[
                "Tests pass or failures are analyzed and documented.",
            ],
            rollback_notes=["Do not proceed to commit or push if validation fails."],
        ),
    ]

    return ImplementationPlan(
        summary=(
            "Implementation plan generated from architecture review context."
        ),
        steps=steps,
        target_files=target_files[:10],
        test_strategy=test_strategy,
        risks=risks,
        assumptions=review.open_questions,
        confidence_score=review.confidence_score,
        source=review.source,
    )


def build_fallback_architecture_review(state: DeliveryState) -> ArchitectureReview:
    return ArchitectureReview.fallback(
        request=state.original_request,
        detected_stack=state.detected_stack,
        likely_files=state.likely_files,
        risky_files=state.repo_risky_files,
    )


def apply_architecture_review_to_state(
    state: DeliveryState,
    review: ArchitectureReview,
) -> None:
    state.architecture_review_summary = review.summary

    if review.detected_stack:
        state.detected_stack = review.detected_stack

    state.affected_areas = review.affected_areas

    if review.likely_files:
        state.likely_files = review.likely_files
    elif review.affected_areas and not state.likely_files:
        state.likely_files = review.affected_areas

    state.architecture_recommended_approach = review.recommended_approach
    state.risk_notes = review.risks
    state.security_notes = review.security_notes
    state.testing_notes = review.testing_notes
    state.devops_notes = review.devops_notes
    state.architecture_open_questions = review.open_questions
    state.architecture_confidence_score = review.confidence_score
    state.architecture_review_source = review.source

    state.mark_completed("architecture_review")
    state.mark_completed("run_architecture_review")
