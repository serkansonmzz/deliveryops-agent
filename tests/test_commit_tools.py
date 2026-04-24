from pathlib import Path
import subprocess

from app.tools.commit_tools import (
    filter_commit_files,
    get_commit_candidate_files,
    create_git_commit,
)


def init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, check=True)


def test_filter_commit_files_excludes_runtime_files():
    files = [
        "README.md",
        "src/app/main.py",
        ".deliveryops/state.json",
        ".venv/pyvenv.cfg",
        ".pytest_cache/cache",
    ]

    result = filter_commit_files(files)

    assert "README.md" in result
    assert "src/app/main.py" in result
    assert ".deliveryops/state.json" not in result
    assert ".venv/pyvenv.cfg" not in result
    assert ".pytest_cache/cache" not in result


def test_create_git_commit(tmp_path: Path):
    init_git_repo(tmp_path)

    readme = tmp_path / "README.md"
    readme.write_text("# Test Project\n", encoding="utf-8")

    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "chore: initial commit"], cwd=tmp_path, check=True)

    readme.write_text("# Test Project\n\nNew documentation.\n", encoding="utf-8")

    candidate_files = get_commit_candidate_files(tmp_path)

    assert "README.md" in candidate_files

    result = create_git_commit(
        repo_path=tmp_path,
        subject="docs: update readme documentation",
        body="Adds a small README documentation update.",
        files=candidate_files,
    )

    assert result.commit_hash
    assert result.subject == "docs: update readme documentation"
    assert "README.md" in result.committed_files

    log_result = subprocess.run(
        ["git", "log", "--oneline", "--max-count=1"],
        cwd=tmp_path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )

    assert "docs: update readme documentation" in log_result.stdout