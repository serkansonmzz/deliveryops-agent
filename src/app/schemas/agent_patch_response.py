from pydantic import BaseModel, Field


class AgentPatchResponse(BaseModel):
    summary: str
    target_files: list[str] = Field(default_factory=list)
    unified_diff: str
    rationale: str