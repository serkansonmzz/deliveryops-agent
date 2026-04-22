from pathlib import Path

from app.schemas.approval_record import ApprovalRecord
from app.tools.approval_tools import (
    render_approval_record,
    append_approval_record,
)


def test_render_approval_record():
    record = ApprovalRecord(
        request_id="req_test",
        action="apply_patch",
        decision="approved",
        reason="Looks safe.",
    )

    markdown = render_approval_record(record)

    assert "Approval Decision: apply_patch" in markdown
    assert "approved" in markdown
    assert "Looks safe." in markdown


def test_append_approval_record(tmp_path: Path):
    record = ApprovalRecord(
        request_id="req_test",
        action="apply_patch",
        decision="approved",
    )

    output_path = append_approval_record(tmp_path, record)

    assert output_path.exists()

    content = output_path.read_text(encoding="utf-8")

    assert "# DeliveryOps Approval History" in content
    assert "apply_patch" in content
    assert "approved" in content