from pydantic import BaseModel, Field


class CICheckResult(BaseModel):
    name: str
    status: str
    conclusion: str | None = None
    url: str | None = None


class CIStatusResult(BaseModel):
    status: str
    summary: str
    checks: list[CICheckResult] = Field(default_factory=list)
    raw_output: str = ""
