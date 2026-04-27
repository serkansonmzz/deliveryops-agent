from typing import Literal

from pydantic import BaseModel, Field


PolicyProfileName = Literal[
    "sandbox",
    "personal_repo",
    "production_repo",
]

PolicyPermission = Literal[
    "safe",
    "approval_required",
    "blocked",
]


class PolicyDecision(BaseModel):
    profile: PolicyProfileName
    action: str
    permission: PolicyPermission
    reason: str
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
