from pydantic import BaseModel, Field


class IssueSpec(BaseModel):
    title: str
    body: str
    labels: list[str] = Field(default_factory=list)