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