from pathlib import Path

from rich.console import Console


console = Console()


def resolve_repo_path(repo: str) -> Path:
    path = Path(repo).expanduser().resolve()

    if not path.exists():
        raise ValueError(f"Repository path does not exist: {path}")

    if not path.is_dir():
        raise ValueError(f"Repository path is not a directory: {path}")

    return path
