from pydantic import BaseModel, Field


class ApprovalRequest(BaseModel):
    action: str
    reason: str
    risk_level: str = "medium"
    affected_files: list[str] = Field(default_factory=list)
    command: str | None = None
    expected_result: str | None = None
    rollback_note: str | None = None
    policy_profile: str | None = None
