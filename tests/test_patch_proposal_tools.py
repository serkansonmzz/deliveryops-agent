from app.tools.patch_proposal_tools import build_patch_proposal


def test_build_patch_proposal_uses_likely_files():
    proposal = build_patch_proposal(
        request="Add branch creation",
        likely_files=["src/app/main.py", "src/app/tools/git_tools.py"],
        implementation_plan=["Inspect files", "Update code", "Run tests"],
    )

    assert proposal.requires_approval is True
    assert proposal.affected_files == ["src/app/main.py", "src/app/tools/git_tools.py"]
    assert proposal.proposed_changes[0] == "Inspect files"


def test_build_patch_proposal_defaults_when_no_likely_files():
    proposal = build_patch_proposal(
        request="Add healthcheck endpoint",
        likely_files=[],
        implementation_plan=[],
    )

    assert proposal.affected_files == ["To be determined during patch generation."]
    assert proposal.risk_level == "low"


def test_build_patch_proposal_marks_delete_as_high_risk():
    proposal = build_patch_proposal(
        request="Delete old deployment files",
        likely_files=["Dockerfile"],
        implementation_plan=["Remove old files"],
    )

    assert proposal.risk_level == "high"