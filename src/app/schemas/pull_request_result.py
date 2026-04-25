from pydantic import BaseModel


class PullRequestResult(BaseModel):
    url: str
    title: str
    base_branch: str
    head_branch: str
    draft: bool = True