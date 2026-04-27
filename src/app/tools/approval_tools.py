from pathlib import Path

from app.schemas.approval_record import ApprovalRecord


def render_approval_record(record: ApprovalRecord) -> str:
    reason = record.reason or "No reason provided."
    lines = [
        f"## Approval Decision: {record.action}",
        "",
        f"- Request ID: `{record.request_id}`",
        f"- Action: `{record.action}`",
        f"- Decision: `{record.decision}`",
        f"- Timestamp: `{record.timestamp}`",
    ]

    if record.risk_level:
        lines.append(f"- Risk Level: `{record.risk_level}`")

    if record.policy_profile:
        lines.append(f"- Policy Profile: `{record.policy_profile}`")

    lines.append("")
    lines.append("### Reason")
    lines.append("")
    lines.append(reason)
    lines.append("")

    if record.command:
        lines.append("### Command")
        lines.append("")
        lines.append(f"`{record.command}`")
        lines.append("")

    if record.affected_files:
        lines.append("### Affected Files")
        lines.append("")
        for file_path in record.affected_files:
            lines.append(f"- `{file_path}`")
        lines.append("")

    if record.expected_result:
        lines.append("### Expected Result")
        lines.append("")
        lines.append(record.expected_result)
        lines.append("")

    if record.rollback_note:
        lines.append("### Rollback Note")
        lines.append("")
        lines.append(record.rollback_note)
        lines.append("")

    return "\n".join(lines) + "\n"

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


def has_approved_action(repo_path: Path, request_id: str, action: str) -> bool:
    approvals_path = repo_path / ".deliveryops" / "approvals.md"

    if not approvals_path.exists():
        return False

    content = approvals_path.read_text(encoding="utf-8")

    return (
        f"- Request ID: `{request_id}`" in content
        and f"- Action: `{action}`" in content
        and "- Decision: `approved`" in content
    )