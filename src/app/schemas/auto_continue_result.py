from pydantic import BaseModel, Field


class AutoContinueResult(BaseModel):
    executed_actions: list[str] = Field(default_factory=list)
    stopped_at_action: str | None = None
    stopped_reason: str
    completed: bool = False