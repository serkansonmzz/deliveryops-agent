from pathlib import Path

from app.schemas.approval_record import ApprovalRecord


def render_approval_record(record: ApprovalRecord) -> str:
    reason = record.reason or "No reason provided."

    return f"""## Approval Decision: {record.action}

- Request ID: `{record.request_id}`
- Action: `{record.action}`
- Decision: `{record.decision}`
- Timestamp: `{record.timestamp}`

### Reason

{reason}

"""


def append_approval_record(repo_path: Path, record: ApprovalRecord) -> Path:
    workspace = repo_path / ".deliveryops"
    workspace.mkdir(exist_ok=True)

    approvals_path = workspace / "approvals.md"

    existing = ""
    if approvals_path.exists():
        existing = approvals_path.read_text(encoding="utf-8")

    if not existing.strip():
        existing = "# DeliveryOps Approval History\n\n"

    approvals_path.write_text(
        existing + render_approval_record(record),
        encoding="utf-8",
    )

    return approvals_path