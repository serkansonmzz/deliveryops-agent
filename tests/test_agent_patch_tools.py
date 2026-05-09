from pathlib import Path
import subprocess

import pytest

from app.schemas.agent_patch_response import AgentPatchResponse
from app.schemas.delivery_state import DeliveryState
from app.tools import agent_patch_tools
from app.tools.agent_patch_tools import build_agent_patch_prompt, generate_patch_with_agent


def init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, check=True)


class FakeResponse:
    def __init__(self, content: AgentPatchResponse):
        self.content = content


class FakeAgent:
    prompts: list[str] = []
    responses: list[AgentPatchResponse] = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def run(self, prompt: str) -> FakeResponse:
        self.prompts.append(prompt)
        return FakeResponse(self.responses.pop(0))


def test_build_agent_patch_prompt_prefers_dev_patch_context():
    context = {
        "request": "Update README",
        "issue_url": "https://example.com/issue/1",
        "branch_name": "feature/test",
        "architecture_review_summary": "Docs-only.",
        "implementation_plan": ["Update README"],
        "likely_files": ["README.md"],
        "files": [{"path": "README.md", "content": "# Demo\n"}],
        "dev_patch_context": "## Request\nUpdate README\n\n## Selected Repository Files\nREADME.md",
    }

    prompt = build_agent_patch_prompt(context)

    assert "DevPatchContext" in prompt
    assert "Update README" in prompt
    assert "Only modify files that are relevant" in prompt


def test_build_agent_patch_prompt_keeps_legacy_fallback():
    context = {
        "request": "Update README",
        "issue_url": "https://example.com/issue/1",
        "branch_name": "feature/test",
        "architecture_review_summary": "Docs-only.",
        "implementation_plan": ["Update README"],
        "likely_files": ["README.md"],
        "files": [{"path": "README.md", "content": "# Demo\n"}],
    }

    prompt = build_agent_patch_prompt(context)

    assert "Generate a unified diff patch for this request" in prompt
    assert "Repository File Context" in prompt


def test_generate_patch_with_agent_retries_invalid_patch(monkeypatch, tmp_path: Path):
    init_git_repo(tmp_path)
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "chore: initial"], cwd=tmp_path, check=True)

    invalid = AgentPatchResponse(
        summary="bad",
        target_files=["README.md"],
        unified_diff="--- a/README.md\n+++ b/README.md\n+# Demo\n",
        rationale="bad",
    )
    valid = AgentPatchResponse(
        summary="good",
        target_files=["README.md"],
        unified_diff=(
            "diff --git a/README.md b/README.md\n"
            "index dab306f..cb7b681 100644\n"
            "--- a/README.md\n"
            "+++ b/README.md\n"
            "@@ -1 +1,3 @@\n"
            " # Demo\n"
            "+\n"
            "+Updated.\n"
        ),
        rationale="good",
    )
    FakeAgent.prompts = []
    FakeAgent.responses = [invalid, valid]
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setattr(agent_patch_tools, "Agent", FakeAgent)

    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Update README.",
        likely_files=["README.md"],
    )

    patch_path = generate_patch_with_agent(tmp_path, state)

    assert patch_path.name == "generated.patch"
    assert len(FakeAgent.prompts) == 2
    assert "Previous patch attempt was rejected" in FakeAgent.prompts[1]
    assert state.dev_context_status == "patch_generated"


def test_generate_patch_with_agent_records_failure_after_retries(
    monkeypatch,
    tmp_path: Path,
):
    init_git_repo(tmp_path)
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "chore: initial"], cwd=tmp_path, check=True)

    invalid = AgentPatchResponse(
        summary="bad",
        target_files=["README.md"],
        unified_diff="--- a/README.md\n+++ b/README.md\n+# Demo\n",
        rationale="bad",
    )
    FakeAgent.prompts = []
    FakeAgent.responses = [invalid, invalid, invalid]
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setattr(agent_patch_tools, "Agent", FakeAgent)

    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Update README.",
        likely_files=["README.md"],
    )

    with pytest.raises(RuntimeError, match="validation retries"):
        generate_patch_with_agent(tmp_path, state)

    assert state.dev_context_status == "patch_generation_failed"
    assert (tmp_path / ".deliveryops" / "rejected.patch").exists()
    assert (tmp_path / ".deliveryops" / "patch_validation_error.txt").exists()
