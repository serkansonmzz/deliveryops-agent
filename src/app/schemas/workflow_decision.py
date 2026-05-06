from pydantic import BaseModel, Field


class WorkflowDecision(BaseModel):
    status: str
    next_action: str | None = None
    next_command: str | None = None
    reason: str
    safe_to_run: bool = False
    requires_approval: bool = False
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
