from pydantic import BaseModel, Field


class AgentRoleSpec(BaseModel):
    role_id: str
    display_name: str
    purpose: str
    responsibilities: list[str] = Field(default_factory=list)
    expected_outputs: list[str] = Field(default_factory=list)
    implemented_capabilities: list[str] = Field(default_factory=list)
    future_capabilities: list[str] = Field(default_factory=list)


class AgentRoleStatus(BaseModel):
    role_id: str
    display_name: str
    status: str
    summary: str
    implemented_capabilities: list[str] = Field(default_factory=list)
    future_capabilities: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
