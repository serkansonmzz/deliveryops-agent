from pathlib import Path
import subprocess

from app.schemas.delivery_state import DeliveryState
from app.services.test_service import detect_tests, run_tests, analyze_failed_tests
from app.state_store import ensure_workspace, save_state


def init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, check=True)


def make_state(repo_path: Path, **kwargs) -> DeliveryState:
    state = DeliveryState(
        request_id="req_test",
        repo_path=str(repo_path),
        original_request="Test service layer",
        **kwargs,
    )
    ensure_workspace(repo_path)
    save_state(state)
    return state


def test_detect_tests_service_detects_python_tests(tmp_path: Path):
    init_git_repo(tmp_path)
    (tmp_path / "tests").mkdir()
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")

    make_state(tmp_path)

    result = detect_tests(tmp_path)

    assert result.status == "detected"
    assert "pytest" in str(result.details.get("command"))


def test_run_tests_service_passes(tmp_path: Path):
    init_git_repo(tmp_path)
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_sample.py").write_text(
        "def test_sample():\n"
        "    assert 1 + 1 == 2\n",
        encoding="utf-8",
    )
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")

    make_state(tmp_path)

    result = run_tests(tmp_path)

    assert result.status == "passed"
    assert result.exit_code == 0


def test_analyze_failed_tests_service_skips_without_failure(tmp_path: Path):
    init_git_repo(tmp_path)
    make_state(tmp_path, test_status="passed")

    result = analyze_failed_tests(tmp_path)

    assert result.status == "skipped"
