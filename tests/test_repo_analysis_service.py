from pathlib import Path
import subprocess

from app.schemas.delivery_state import DeliveryState
from app.services.repo_analysis_service import run_repo_analysis
from app.state_store import ensure_workspace, load_state, save_state


def init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, check=True)


def test_run_repo_analysis_updates_state(tmp_path: Path):
    init_git_repo(tmp_path)
    (tmp_path / "src" / "app").mkdir(parents=True)
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / "app" / "main.py").write_text(
        "print('hi')\n",
        encoding="utf-8",
    )
    (tmp_path / "tests" / "test_main.py").write_text(
        "def test_x(): assert True\n",
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname='x'\n",
        encoding="utf-8",
    )
    ensure_workspace(tmp_path)
    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Update README documentation",
    )
    save_state(state)

    result = run_repo_analysis(tmp_path)
    updated = load_state(tmp_path)

    assert result.status == "analyzed"
    assert updated.repo_analysis_summary
    assert updated.repo_source_file_count == 1
    assert updated.repo_test_file_count == 1
    assert "README.md" in updated.likely_files
    assert "analyze_repository" in updated.completed_steps
