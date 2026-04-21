from pydantic import BaseModel, Field


class ArchitectureReview(BaseModel):
    summary: str
    detected_stack: list[str] = Field(default_factory=list)
    affected_areas: list[str] = Field(default_factory=list)
    likely_files: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    security_notes: list[str] = Field(default_factory=list)
    testing_notes: list[str] = Field(default_factory=list)
    devops_notes: list[str] = Field(default_factory=list)
    confidence: str = "medium"