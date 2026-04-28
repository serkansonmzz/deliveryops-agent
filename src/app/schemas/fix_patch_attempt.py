from pydantic import BaseModel, Field


class FixPatchAttempt(BaseModel):
    attempt_number: int
    source: str = "test_failure"
    status: str
    summary: str
    target_files: list[str] = Field(default_factory=list)
    generated_patch_path: str | None = None
    rejected_patch_path: str | None = None
    error: str | None = None
