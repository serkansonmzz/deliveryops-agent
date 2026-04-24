from pydantic import BaseModel, Field


class CommitMessageSpec(BaseModel):
    subject: str
    body: str | None = None
    changed_files: list[str] = Field(default_factory=list)
    diff_summary: str | None = None
    rationale: str | None = None