from pydantic import BaseModel, Field


class PatchProposal(BaseModel):
    summary: str
    affected_files: list[str] = Field(default_factory=list)
    proposed_changes: list[str] = Field(default_factory=list)
    risk_level: str = "medium"
    requires_approval: bool = True