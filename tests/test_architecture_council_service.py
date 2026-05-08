from pathlib import Path
import subprocess
from types import SimpleNamespace

from app.schemas.delivery_state import DeliveryState
from app.services import architecture_council_service
from app.services.architecture_council_service import (
    build_architecture_council_prompt,
    run_architecture_council_agent,
)
from app.state_store import ensure_workspace, load_state, save_state


def init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, check=True)


def test_build_architecture_council_prompt_includes_repo_context(tmp_path: Path):
    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Update README docs",
        detected_stack=["python"],
        likely_files=["README.md"],
        repo_analysis_summary="Repo has docs and Python source.",
        repo_risky_files=[".github/workflows/ci.yml"],
        repo_source_test_map={"src/app/main.py": ["tests/test_main.py"]},
    )

    prompt = build_architecture_council_prompt(state)

    assert "Update README docs" in prompt
    assert "README.md" in prompt
    assert "Repo has docs and Python source." in prompt
    assert ".github/workflows/ci.yml" in prompt
    assert "tests/test_main.py" in prompt


def test_run_architecture_council_agent_fallback_updates_state(tmp_path: Path):
    init_git_repo(tmp_path)
    ensure_workspace(tmp_path)
    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Update README docs",
        detected_stack=["python"],
        likely_files=["README.md"],
        repo_analysis_summary="Repo has docs and Python source.",
    )
    save_state(state)

    result = run_architecture_council_agent(tmp_path, use_llm=False)
    updated = load_state(tmp_path)

    assert result.status == "reviewed"
    assert updated.architecture_review_summary
    assert updated.architecture_review_source == "fallback"
    assert updated.architecture_confidence_score is not None
    assert "architecture_review" in updated.completed_steps


def test_run_architecture_council_agent_falls_back_on_invalid_agent_output(
    monkeypatch,
    tmp_path: Path,
):
    init_git_repo(tmp_path)
    ensure_workspace(tmp_path)
    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Update README docs",
        likely_files=["README.md"],
    )
    save_state(state)

    class FakeAgent:
        def run(self, prompt: str):
            return SimpleNamespace(content="not structured")

    monkeypatch.setattr(
        architecture_council_service,
        "build_agno_agent",
        lambda definition: FakeAgent(),
    )

    result = run_architecture_council_agent(tmp_path, use_llm=True)
    updated = load_state(tmp_path)

    assert result.status == "reviewed"
    assert updated.architecture_review_source == "fallback"
