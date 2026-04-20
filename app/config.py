from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv
import os


class Settings(BaseModel):
    app_name: str = "DeliveryOps Agent"
    openai_api_key: str | None = None
    github_token: str | None = None


def load_settings() -> Settings:
    load_dotenv()

    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        github_token=os.getenv("GITHUB_TOKEN"),
    )


def resolve_repo_path(repo: str) -> Path:
    path = Path(repo).expanduser().resolve()

    if not path.exists():
        raise ValueError(f"Repository path does not exist: {path}")

    if not path.is_dir():
        raise ValueError(f"Repository path is not a directory: {path}")

    return path