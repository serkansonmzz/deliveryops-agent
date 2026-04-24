from datetime import datetime, timezone
from pathlib import Path
from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class DeliveryState(BaseModel):
    request_id: str
    repo_path: str
    github_owner: str | None = None
    github_repo: str | None = None
    github_issue_number: int | None = None
    github_issue_url: str | None = None
    branch_name: str | None = None

    original_request: str
    current_step: str = "initialized"
    completed_steps: list[str] = Field(default_factory=list)

    pending_action: str | None = None
    pending_approval: bool = False

    test_status: str | None = None
    test_command: str | None = None
    changed_files: list[str] = Field(default_factory=list)

    architecture_review_summary: str | None = None
    detected_stack: list[str] = Field(default_factory=list)
    affected_areas: list[str] = Field(default_factory=list)
    likely_files: list[str] = Field(default_factory=list)
    risk_notes: list[str] = Field(default_factory=list)
    security_notes: list[str] = Field(default_factory=list)
    testing_notes: list[str] = Field(default_factory=list)
    devops_notes: list[str] = Field(default_factory=list)
    patch_summary: str | None = None
    patch_affected_files: list[str] = Field(default_factory=list)
    proposed_changes: list[str] = Field(default_factory=list)
    patch_risk_level: str | None = None
    implementation_plan: list[str] = Field(default_factory=list)
    commit_message: str | None = None
    commit_body: str | None = None
    commit_rationale: str | None = None
    commit_diff_summary: str | None = None
    commit_files: list[str] = Field(default_factory=list)
    committed_files: list[str] = Field(default_factory=list)
    commit_hash: str | None = None

    push_remote: str | None = None
    push_branch: str | None = None
    push_status: str | None = None
    push_output: str | None = None

    last_error: str | None = None
    pr_url: str | None = None

    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)

    def mark_completed(self, step: str) -> None:
        if step not in self.completed_steps:
            self.completed_steps.append(step)

        self.current_step = step
        self.updated_at = utc_now_iso()

    @property
    def workspace_dir(self) -> Path:
        return Path(self.repo_path) / ".deliveryops"