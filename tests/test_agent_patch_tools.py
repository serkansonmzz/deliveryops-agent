from app.tools.agent_patch_tools import build_agent_patch_prompt


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
