from pathlib import Path

import pytest

from app.schemas.delivery_state import DeliveryState
from app.tools import issue_comment_tools


def test_ensure_issue_available_rejects_missing_issue_number():
    state = DeliveryState(
        request_id="req_test",
        repo_path="/tmp/repo",
        original_request="Add issue comments",
        github_owner="test-owner",
        github_repo="test-repo",
    )

    with pytest.raises(RuntimeError):
        issue_comment_tools.ensure_issue_available(state)


def test_post_progress_comment(monkeypatch, tmp_path: Path):
    def fake_add_github_issue_comment(owner, repo, issue_number, body):
        assert owner == "test-owner"
        assert repo == "test-repo"
        assert issue_number == 7
        assert "DeliveryOps Progress Update" in body

        return "https://github.com/test-owner/test-repo/issues/7#issuecomment-1"

    monkeypatch.setattr(
        issue_comment_tools,
        "add_github_issue_comment",
        fake_add_github_issue_comment,
    )

    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Add issue comments",
        github_owner="test-owner",
        github_repo="test-repo",
        github_issue_number=7,
    )

    result = issue_comment_tools.post_progress_comment(tmp_path, state)

    assert result.endswith("issuecomment-1")