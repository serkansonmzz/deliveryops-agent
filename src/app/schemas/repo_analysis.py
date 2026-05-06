from pydantic import BaseModel, Field


class FileSignal(BaseModel):
    path: str
    kind: str
    score: int = 0
    reasons: list[str] = Field(default_factory=list)


class RepoAnalysisResult(BaseModel):
    detected_stack: list[str] = Field(default_factory=list)
    source_files: list[str] = Field(default_factory=list)
    test_files: list[str] = Field(default_factory=list)
    documentation_files: list[str] = Field(default_factory=list)
    config_files: list[str] = Field(default_factory=list)
    risky_files: list[str] = Field(default_factory=list)
    likely_files: list[FileSignal] = Field(default_factory=list)
    source_test_map: dict[str, list[str]] = Field(default_factory=dict)
    summary: str
