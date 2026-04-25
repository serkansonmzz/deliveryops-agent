from pydantic import BaseModel, Field


class FinalReport(BaseModel):
    title: str
    body: str
    changed_files: list[str] = Field(default_factory=list)
    issue_url: str | None = None
    pr_url: str | None = None
    commit_hash: str | None = None