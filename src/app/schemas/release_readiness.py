from pydantic import BaseModel, Field


class ReleaseReadinessResult(BaseModel):
    status: str
    risk_level: str
    summary: str
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
