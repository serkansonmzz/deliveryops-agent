import subprocess
from pathlib import Path

from app.schemas.approval_record import ApprovalRecord
from app.schemas.delivery_state import DeliveryState
from app.schemas.smoke_test_result import SmokeTestResult
from app.state_store import ensure_workspace, save_state
from app.tools.approval_tools import append_approval_record
from app.tools.apply_patch_tools import apply_available_patch
from app.tools.commit_message_tools import build_commit_message_spec
from app.tools.commit_tools import create_git_commit, get_commit_candidate_files
from app.tools.delivery_report_tools import build_final_report, write_final_report
from app.tools.git_tools import create_branch, get_current_branch
from app.tools.markdown_tracking_tools import update_delivery_markdown
from app.tools.patch_generator_tools import generate_patch
from app.tools.push_tools import push_current_branch


def run_command(args: list[str], cwd: Path) -> None:
    result = subprocess.run(
        args,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(args)}\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )


def initialize_smoke_git_repo(repo_path: Path, remote_path: Path) -> None:
    repo_path.mkdir(parents=True, exist_ok=True)

    run_command(["git", "init"], cwd=repo_path)
    run_command(["git", "config", "user.email", "smoke@example.com"], cwd=repo_path)
    run_command(["git", "config", "user.name", "Smoke Test"], cwd=repo_path)

    readme_path = repo_path / "README.md"
    readme_path.write_text(
        "# Smoke Test Project\n\n"
        "This repository is created by DeliveryOps smoke test.\n",
        encoding="utf-8",
    )

    run_command(["git", "add", "README.md"], cwd=repo_path)
    run_command(["git", "commit", "-m", "chore: initial smoke repo"], cwd=repo_path)

    run_command(["git", "init", "--bare", str(remote_path)], cwd=repo_path)
    run_command(["git", "remote", "add", "origin", str(remote_path)], cwd=repo_path)


def append_approval(repo_path: Path, state: DeliveryState, action: str, reason: str) -> None:
    append_approval_record(
        repo_path,
        ApprovalRecord(
            request_id=state.request_id,
            action=action,
            decision="approved",
            reason=reason,
        ),
    )


def run_local_smoke_test(workspace_path: Path) -> SmokeTestResult:
    workspace_path.mkdir(parents=True, exist_ok=True)

    repo_path = workspace_path / "repo"
    remote_path = workspace_path / "remote.git"

    initialize_smoke_git_repo(repo_path, remote_path)

    request = "Update README documentation for DeliveryOps smoke testing."
    branch_name = "feature/smoke-e2e"

    create_branch(repo_path, branch_name)

    state = DeliveryState(
        request_id="req_smoke_test",
        repo_path=str(repo_path),
        original_request=request,
        branch_name=branch_name,
        github_issue_url="local-smoke-test",
    )

    ensure_workspace(repo_path)

    state.mark_completed("inspect_repository")
    state.mark_completed("initialize_workspace")
    state.mark_completed("create_feature_branch")

    save_state(state)
    update_delivery_markdown(state)

    patch_path = generate_patch(repo_path, state)

    if patch_path is None:
        raise RuntimeError("Smoke test failed: deterministic patch was not generated.")

    state.patch_summary = "Smoke test generated a deterministic README patch."
    state.patch_affected_files = ["README.md"]
    state.proposed_changes = ["Update README documentation for smoke testing."]
    state.mark_completed("prepare_patch")

    append_approval(
        repo_path,
        state,
        action="apply_patch",
        reason="Smoke test approved apply_patch.",
    )

    patch_result = apply_available_patch(repo_path, state)

    if hasattr(patch_result, "changed_files"):
        for changed_file in patch_result.changed_files:
            if changed_file not in state.changed_files:
                state.changed_files.append(changed_file)

    state.mark_completed("apply_patch")

    commit_spec = build_commit_message_spec(repo_path, state)

    state.commit_message = commit_spec.subject
    state.commit_body = commit_spec.body
    state.commit_diff_summary = commit_spec.diff_summary
    state.commit_rationale = commit_spec.rationale
    state.changed_files = commit_spec.changed_files
    state.mark_completed("generate_commit_message")

    append_approval(
        repo_path,
        state,
        action="git_commit",
        reason="Smoke test approved git_commit.",
    )

    candidate_files = get_commit_candidate_files(repo_path)

    commit_result = create_git_commit(
        repo_path=repo_path,
        subject=state.commit_message,
        body=state.commit_body,
        files=candidate_files,
    )

    state.commit_hash = commit_result.commit_hash
    state.committed_files = commit_result.committed_files
    state.changed_files = commit_result.committed_files
    state.mark_completed("commit_changes")

    append_approval(
        repo_path,
        state,
        action="git_push",
        reason="Smoke test approved git_push.",
    )

    push_result = push_current_branch(repo_path)

    state.push_remote = push_result.remote
    state.pushed_branch = push_result.branch_name
    state.push_status = "pushed"
    state.push_output = push_result.stdout or push_result.stderr or "Push completed."
    state.mark_completed("push_branch")

    report = build_final_report(state)
    report_path = write_final_report(repo_path, report)

    state.final_report_path = str(report_path.relative_to(repo_path))
    state.final_report_status = "generated"
    state.mark_completed("generate_final_report")

    save_state(state)
    update_delivery_markdown(state)

    current_branch = get_current_branch(repo_path)

    return SmokeTestResult(
        passed=True,
        workspace_path=str(workspace_path),
        repo_path=str(repo_path),
        remote_path=str(remote_path),
        branch_name=current_branch,
        commit_hash=state.commit_hash,
        pushed=True,
        final_report_path=str(report_path),
        notes=[
            "Local smoke repo created.",
            "Patch generated and applied.",
            "Commit message generated.",
            "Commit created.",
            "Branch pushed to local bare remote.",
            "Final report generated.",
        ],
    )