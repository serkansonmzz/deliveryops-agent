from pydantic import BaseModel


class PushResult(BaseModel):
    remote: str
    branch_name: str
    pushed: bool
    stdout: str = ""
    stderr: str = ""