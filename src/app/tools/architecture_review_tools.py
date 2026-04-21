from pathlib import Path

from app.schemas.architecture_review import ArchitectureReview
from app.schemas.implementation_plan import ImplementationPlan
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
    steps = [
        "Review the generated GitHub issue and confirm the requested scope.",
        "Inspect the likely affected files identified by the architecture review.",
        "Make the smallest code change that satisfies the request.",
        "Update or add focused tests for the new behavior.",
        "Run the relevant test command and review the output.",
        "Update DeliveryOps tracking files with the implementation result.",
        "Prepare a conventional commit message after tests pass.",
    ]

    if "Git workflow automation" in review.affected_areas:
        steps.insert(3, "Be careful with branch-changing Git operations and preserve workflow state.")

    if "GitHub workflow integration" in review.affected_areas:
        steps.insert(3, "Verify GitHub CLI commands against the installed gh version.")

    return ImplementationPlan(steps=steps)