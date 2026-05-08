from pathlib import Path
import subprocess
from types import SimpleNamespace

from app.schemas.delivery_state import DeliveryState
from app.services import implementation_plan_service
from app.services.implementation_plan_service import (
    build_implementation_plan_prompt,
    run_implementation_planner_agent,
)
from app.state_store import ensure_workspace, load_state, save_state


def init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, check=True)


def test_build_implementation_plan_prompt_includes_architecture_context(tmp_path: Path):
    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Update README docs",
        likely_files=["README.md"],
        repo_analysis_summary="Repo has docs and Python source.",
        architecture_review_summary="Docs-only change with low runtime risk.",
        architecture_recommended_approach=["Keep it minimal."],
        risk_notes=["Review generated docs."],
        testing_notes=["Run pytest."],
        repo_source_test_map={"src/app/main.py": ["tests/test_main.py"]},
    )

    prompt = build_implementation_plan_prompt(state)

    assert "Update README docs" in prompt
    assert "README.md" in prompt
    assert "Docs-only change" in prompt
    assert "Keep it minimal" in prompt
    assert "tests/test_main.py" in prompt


def test_run_implementation_planner_agent_fallback_updates_state(tmp_path: Path):
    init_git_repo(tmp_path)
    ensure_workspace(tmp_path)
    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Update README docs",
        likely_files=["README.md"],
        testing_notes=["Run pytest."],
        risk_notes=["Docs-only change."],
    )
    save_state(state)

    result = run_implementation_planner_agent(tmp_path, use_llm=False)
    updated = load_state(tmp_path)

    assert result.status == "planned"
    assert updated.implementation_plan_summary
    assert updated.implementation_plan_source == "fallback"
    assert updated.implementation_plan_steps
    assert updated.implementation_plan
    assert "implementation_plan" in updated.completed_steps


def test_run_implementation_planner_agent_falls_back_on_invalid_agent_output(
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
        implementation_plan_service,
        "build_agno_agent",
        lambda definition: FakeAgent(),
    )

    result = run_implementation_planner_agent(tmp_path, use_llm=True)
    updated = load_state(tmp_path)

    assert result.status == "planned"
    assert updated.implementation_plan_source == "fallback"
