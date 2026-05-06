from app.schemas.feature_request import FeatureRequest
from app.schemas.issue_spec import IssueSpec


def build_issue_title(request: str) -> str:
    cleaned = " ".join(request.strip().split())

    if not cleaned:
        return "DeliveryOps feature request"

    if len(cleaned) <= 80:
        return cleaned

    return cleaned[:77].rstrip() + "..."


def build_issue_body(request: str) -> str:
    cleaned = request.strip()

    return f"""# DeliveryOps Feature Request

## Problem

A new feature request was submitted through DeliveryOps Agent.

## Request

{cleaned}

## Goal

Implement the requested change in a small, reviewable, and testable way.

## Scope

- Analyze the existing repository structure.
- Identify the files likely affected by this request.
- Prepare an implementation plan.
- Apply code changes only after approval.
- Run relevant tests.
- Prepare the work for commit, push, and draft pull request.

## Out of Scope

- Automatic merge.
- Production deployment.
- Destructive Git operations.
- Secret or environment file modification without explicit approval.

## Acceptance Criteria

- The requested behavior is implemented.
- Relevant tests are added or updated where appropriate.
- Existing tests pass.
- The change is explained clearly in the delivery report.
- The final work can be reviewed through a pull request.

## Definition of Done

- DeliveryOps workflow state is updated.
- `.deliveryops/DELIVERY.md` reflects the latest progress.
- GitHub issue is updated with progress comments where needed.
- Tests are executed or a clear reason is provided if tests cannot be run.

## Risk Notes

- This issue was generated automatically from a user request.
- Technical scope may be refined during architecture review.
"""


def build_issue_spec(request: str) -> IssueSpec:
    feature_request = FeatureRequest.from_raw_request(request)
    issue_spec = IssueSpec.from_feature_request(
        request_title=feature_request.title,
        request_summary=feature_request.summary,
    )
    return ensure_issue_spec_has_body(issue_spec)


def normalize_list(items: list[str], fallback: str) -> list[str]:
    cleaned = [item.strip() for item in items if item and item.strip()]
    return cleaned or [fallback]


def render_bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def build_issue_body_from_feature_request(feature_request: FeatureRequest) -> str:
    constraints = normalize_list(
        feature_request.constraints,
        "No explicit constraints provided.",
    )
    assumptions = normalize_list(
        feature_request.assumptions,
        "No assumptions recorded.",
    )
    risks = normalize_list(
        feature_request.initial_risks,
        "No initial risks identified.",
    )

    return "\n".join(
        [
            "## Problem",
            "",
            feature_request.problem or feature_request.summary,
            "",
            "## Goal",
            "",
            feature_request.goal,
            "",
            "## Constraints",
            "",
            render_bullets(constraints),
            "",
            "## Assumptions",
            "",
            render_bullets(assumptions),
            "",
            "## Initial Risks",
            "",
            render_bullets(risks),
        ]
    )


def build_issue_body_from_issue_spec(issue_spec: IssueSpec) -> str:
    if issue_spec.body.strip():
        return issue_spec.body.strip() + "\n"

    return "\n".join(
        [
            "## Acceptance Criteria",
            "",
            render_bullets(
                normalize_list(
                    issue_spec.acceptance_criteria,
                    "Acceptance criteria should be clarified.",
                )
            ),
            "",
            "## Definition of Done",
            "",
            render_bullets(
                normalize_list(
                    issue_spec.definition_of_done,
                    "Definition of done should be clarified.",
                )
            ),
            "",
            "## Technical Notes",
            "",
            render_bullets(
                normalize_list(
                    issue_spec.technical_notes,
                    "No technical notes provided.",
                )
            ),
            "",
            "## Risk Notes",
            "",
            render_bullets(
                normalize_list(
                    issue_spec.risk_notes,
                    "No risk notes provided.",
                )
            ),
        ]
    )


def ensure_issue_spec_has_body(issue_spec: IssueSpec) -> IssueSpec:
    if issue_spec.body.strip():
        return issue_spec

    return issue_spec.model_copy(
        update={"body": build_issue_body_from_issue_spec(issue_spec)}
    )
