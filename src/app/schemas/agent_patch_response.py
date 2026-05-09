from pydantic import BaseModel, Field


class FileEditIntent(BaseModel):
    path: str
    edit_type: str
    content: str
    anchor: str | None = None
    replacement: str | None = None
    rationale: str | None = None


class AgentPatchResponse(BaseModel):
    summary: str
    target_files: list[str] = Field(default_factory=list)
    unified_diff: str = ""
    file_edits: list[FileEditIntent] = Field(default_factory=list)
    generation_mode: str = "unified_diff"
    confidence_score: float = 0.5
    rationale: str
