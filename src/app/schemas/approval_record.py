from datetime import datetime, timezone
from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ApprovalRecord(BaseModel):
    request_id: str
    action: str
    decision: str
    reason: str | None = None
    timestamp: str = Field(default_factory=utc_now_iso)
    risk_level: str | None = None
    affected_files: list[str] = Field(default_factory=list)
    command: str | None = None
    expected_result: str | None = None
    rollback_note: str | None = None
    policy_profile: str | None = None