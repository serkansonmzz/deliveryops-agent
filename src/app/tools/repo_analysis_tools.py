from pathlib import Path


IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".deliveryops",
    "node_modules",
    "dist",
    "build",
}


def list_repo_files(repo_path: Path, max_files: int = 300) -> list[str]:
    files: list[str] = []

    for path in repo_path.rglob("*"):
        if not path.is_file():
            continue

        relative = path.relative_to(repo_path)

        if any(part in IGNORED_DIRS for part in relative.parts):
            continue

        files.append(str(relative))

        if len(files) >= max_files:
            break

    return sorted(files)


def detect_project_stack(repo_path: Path) -> list[str]:
    stack: list[str] = []

    if (repo_path / "pyproject.toml").exists():
        stack.append("python")

    if (repo_path / "package.json").exists():
        stack.append("nodejs")

    if (repo_path / "Dockerfile").exists():
        stack.append("docker")

    if (repo_path / "docker-compose.yml").exists() or (repo_path / "compose.yml").exists():
        stack.append("docker-compose")

    if (repo_path / ".github" / "workflows").exists():
        stack.append("github-actions")

    if (repo_path / "README.md").exists():
        stack.append("readme")

    return stack


def find_likely_files(repo_path: Path, request: str) -> list[str]:
    files = list_repo_files(repo_path)
    request_lower = request.lower()

    likely: list[str] = []

    keyword_map = {
        "cli": ["main.py", "cli.py", "commands.py"],
        "command": ["main.py", "cli.py", "commands.py"],
        "github": ["github_tools.py", "main.py"],
        "issue": ["github_tools.py", "issue_body_tools.py", "main.py"],
        "branch": ["branch_name_tools.py", "git_tools.py", "main.py"],
        "git": ["git_tools.py", "branch_name_tools.py", "main.py"],
        "test": ["test_", "tests/"],
        "readme": ["README.md"],
        "markdown": ["markdown_tracking_tools.py"],
        "delivery": ["delivery_state.py", "markdown_tracking_tools.py", "main.py"],
        "state": ["delivery_state.py", "state_store.py"],
    }

    for keyword, patterns in keyword_map.items():
        if keyword not in request_lower:
            continue

        for file_path in files:
            if any(pattern in file_path for pattern in patterns):
                likely.append(file_path)

    return sorted(set(likely))[:20]