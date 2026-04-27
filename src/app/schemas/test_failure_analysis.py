from pydantic import BaseModel, Field


class TestFailureAnalysis(BaseModel):
    category: str
    summary: str
    likely_causes: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    risk_level: str = "medium"