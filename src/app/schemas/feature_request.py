from pydantic import BaseModel, Field


class FeatureRequest(BaseModel):
    title: str
    summary: str
    problem: str | None = None
    goal: str
    constraints: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    initial_risks: list[str] = Field(default_factory=list)
