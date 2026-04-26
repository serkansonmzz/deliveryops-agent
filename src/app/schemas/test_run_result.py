from pydantic import BaseModel


class TestRunResult(BaseModel):
    command: str
    status: str
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    summary: str
