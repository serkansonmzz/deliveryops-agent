from pydantic import BaseModel, Field


class CommitResult(BaseModel):
    commit_hash: str
    subject: str
    body: str | None = None
    committed_files: list[str] = Field(default_factory=list)