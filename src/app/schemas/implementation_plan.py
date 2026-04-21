from pydantic import BaseModel, Field


class ImplementationPlan(BaseModel):
    steps: list[str] = Field(default_factory=list)