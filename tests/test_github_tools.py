from app.tools import github_tools
from app.tools.github_tools import GitHubCommandResult


def test_create_github_issue(monkeypatch):
    def fake_run_gh(args, cwd=None):
        if args == ["--version"]:
            return GitHubCommandResult(
                command=["gh", "--version"],
                return_code=0,
                stdout="gh version 2.x",
                stderr="",
            )

        if args == ["auth", "status"]:
            return GitHubCommandResult(
                command=["gh", "auth", "status"],
                return_code=0,
                stdout="Logged in",
                stderr="",
            )

        return GitHubCommandResult(
            command=["gh", *args],
            return_code=0,
            stdout="https://github.com/test-owner/test-repo/issues/12",
            stderr="",
        )

    monkeypatch.setattr(github_tools, "run_gh", fake_run_gh)

    issue = github_tools.create_github_issue(
        owner="test-owner",
        repo="test-repo",
        title="Test issue",
        body="Test body",
        labels=["deliveryops"],
    )

    assert issue.number == 12
    assert issue.title == "Test issue"
    assert issue.url.endswith("/issues/12")


def test_add_github_issue_comment(monkeypatch):
    def fake_run_gh(args, cwd=None):
        if args == ["--version"]:
            return GitHubCommandResult(
                command=["gh", "--version"],
                return_code=0,
                stdout="gh version 2.x",
                stderr="",
            )

        if args == ["auth", "status"]:
            return GitHubCommandResult(
                command=["gh", "auth", "status"],
                return_code=0,
                stdout="Logged in",
                stderr="",
            )

        return GitHubCommandResult(
            command=["gh", *args],
            return_code=0,
            stdout="https://github.com/test-owner/test-repo/issues/12#issuecomment-1",
            stderr="",
        )

    monkeypatch.setattr(github_tools, "run_gh", fake_run_gh)

    result = github_tools.add_github_issue_comment(
        owner="test-owner",
        repo="test-repo",
        issue_number=12,
        body="Progress update",
    )

    assert "issuecomment" in result