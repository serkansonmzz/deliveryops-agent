from pydantic import BaseModel, Field


class ContinueDecision(BaseModel):
    status: str
    next_action: str | None = None
    next_command: str | None = None
    reason: str
    safe_to_run: bool = False
    notes: list[str] = Field(default_factory=list)