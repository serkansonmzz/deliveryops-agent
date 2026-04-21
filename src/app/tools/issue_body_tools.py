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
    return IssueSpec(
        title=build_issue_title(request),
        body=build_issue_body(request),
        labels=[],
    )