from pydantic import BaseModel, Field


class FeatureRequest(BaseModel):
    title: str
    summary: str
    problem: str | None = None
    goal: str
    constraints: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    initial_risks: list[str] = Field(default_factory=list)

    @classmethod
    def from_raw_request(cls, raw_request: str) -> "FeatureRequest":
        cleaned = raw_request.strip()

        if not cleaned:
            cleaned = "Untitled delivery request"

        title = cleaned.splitlines()[0][:80].strip()

        return cls(
            title=title or "Untitled delivery request",
            summary=cleaned,
            problem=None,
            goal=cleaned,
            assumptions=["Generated from raw request fallback."],
            initial_risks=["Request was not fully structured by an agent."],
        )
