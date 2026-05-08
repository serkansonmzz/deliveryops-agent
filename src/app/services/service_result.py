from pydantic import BaseModel, Field


class ServiceResult(BaseModel):
    status: str
    message: str
    exit_code: int = 0
    details: dict[str, str | int | float | bool | None] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
