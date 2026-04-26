from pydantic import BaseModel, Field


class SmokeTestResult(BaseModel):
    passed: bool
    workspace_path: str
    repo_path: str
    remote_path: str
    branch_name: str
    commit_hash: str | None = None
    pushed: bool = False
    final_report_path: str | None = None
    notes: list[str] = Field(default_factory=list)