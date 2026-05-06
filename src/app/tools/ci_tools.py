import json
from pathlib import Path

from app.adapters.github_cli_adapter import (
    ensure_gh_authenticated,
    get_current_branch_pr_json,
    get_pr_checks,
    get_pr_checks_json,
)
from app.schemas.ci_status import CICheckResult, CIStatusResult
from app.schemas.delivery_state import DeliveryState
from app.tools.git_tools import get_current_branch


def normalize_check_state(state: str | None, conclusion: str | None) -> str:
    raw_state = (state or "").lower()
    raw_conclusion = (conclusion or "").lower()

    failed_values = {"failure", "failed", "cancelled", "timed_out", "action_required"}
    passed_values = {"success", "passed", "skipped", "neutral"}
    pending_values = {
        "pending",
        "queued",
        "in_progress",
        "waiting",
        "requested",
        "expected",
    }

    if raw_conclusion in failed_values or raw_state in failed_values:
        return "failed"

    if raw_conclusion in passed_values or raw_state in passed_values:
        return "passed"

    if raw_state in pending_values or raw_conclusion in pending_values:
        return "pending"

    return "unknown"


def parse_pr_checks_json_output(raw_output: str) -> CIStatusResult:
    if not raw_output.strip():
        return CIStatusResult(
            status="no_checks",
            summary="No GitHub checks were found for this pull request.",
            checks=[],
            raw_output=raw_output,
        )

    try:
        payload = json.loads(raw_output)
    except json.JSONDecodeError as exc:
        return CIStatusResult(
            status="unknown",
            summary="Could not parse GitHub checks JSON output.",
            raw_output=raw_output,
            error=str(exc),
        )

    if not isinstance(payload, list):
        return CIStatusResult(
            status="unknown",
            summary="Unexpected GitHub checks JSON shape.",
            raw_output=raw_output,
            error="Expected a list of check objects.",
        )

    checks: list[CICheckResult] = []

    for item in payload:
        if not isinstance(item, dict):
            continue

        name = str(item.get("name") or "unnamed check")
        state = item.get("state")
        conclusion = item.get("conclusion")
        url = item.get("link")
        normalized = normalize_check_state(
            str(state) if state is not None else None,
            str(conclusion) if conclusion is not None else None,
        )

        checks.append(
            CICheckResult(
                name=name,
                status=normalized,
                conclusion=str(conclusion) if conclusion is not None else None,
                url=str(url) if url else None,
                details=str(state) if state is not None else None,
            )
        )

    if not checks:
        return CIStatusResult(
            status="no_checks",
            summary="No GitHub checks were found for this pull request.",
            checks=[],
            raw_output=raw_output,
        )

    failed = [check for check in checks if check.status == "failed"]
    pending = [check for check in checks if check.status in {"pending", "unknown"}]

    if failed:
        return CIStatusResult(
            status="failed",
            summary=f"GitHub CI checks failed. Failed checks: {len(failed)}.",
            checks=checks,
            raw_output=raw_output,
        )

    if pending:
        return CIStatusResult(
            status="pending",
            summary=(
                "GitHub CI checks are pending or unknown. "
                f"Pending checks: {len(pending)}."
            ),
            checks=checks,
            raw_output=raw_output,
        )

    return CIStatusResult(
        status="passed",
        summary=f"All GitHub CI checks passed. Checks: {len(checks)}.",
        checks=checks,
        raw_output=raw_output,
    )


def parse_pr_checks_output(raw_output: str) -> CIStatusResult:
    lines = [line.strip() for line in raw_output.splitlines() if line.strip()]

    if not lines:
        return CIStatusResult(
            status="no_checks",
            summary="No GitHub checks were found for this pull request.",
            checks=[],
            raw_output=raw_output,
        )

    checks: list[CICheckResult] = []
    failed: list[str] = []
    pending: list[str] = []

    for line in lines:
        lower = line.lower()

        if "fail" in lower or "failure" in lower or "cancel" in lower:
            status = "failed"
            failed.append(line)
        elif "pending" in lower or "progress" in lower or "queued" in lower or "waiting" in lower:
            status = "pending"
            pending.append(line)
        elif "pass" in lower or "success" in lower:
            status = "passed"
        else:
            status = "unknown"
            pending.append(line)

        checks.append(
            CICheckResult(
                name=line,
                status=status,
                conclusion=status,
            )
        )

    if failed:
        overall_status = "failed"
        summary = f"CI checks failed. Failed checks: {len(failed)}."
    elif pending:
        overall_status = "pending"
        summary = f"CI checks are still pending or unknown. Pending checks: {len(pending)}."
    else:
        overall_status = "passed"
        summary = f"All detected CI checks passed. Checks: {len(checks)}."

    return CIStatusResult(
        status=overall_status,
        summary=summary,
        checks=checks,
        raw_output=raw_output,
    )


def check_pull_request_ci_status(
    repo_path: Path,
    state: DeliveryState,
) -> CIStatusResult:
    try:
        ensure_gh_authenticated(repo_path)
    except RuntimeError as exc:
        return CIStatusResult(
            status="unavailable",
            summary="GitHub CLI is unavailable or not authenticated.",
            error=str(exc),
        )

    branch = state.pr_head_branch or state.pushed_branch or get_current_branch(repo_path)

    if not branch:
        return CIStatusResult(
            status="unavailable",
            summary="Cannot check CI status because no branch was detected.",
            error="No branch detected.",
        )

    pr_result = get_current_branch_pr_json(branch, repo_path)

    if not pr_result.ok:
        return CIStatusResult(
            status="no_pr",
            summary=(
                f"No pull request was found for branch `{branch}` "
                "or GitHub CLI could not read it."
            ),
            raw_output=pr_result.combined_output,
            error=pr_result.combined_output,
        )

    json_result = get_pr_checks_json(branch=branch, cwd=repo_path)

    if json_result.ok:
        parsed = parse_pr_checks_json_output(json_result.stdout)
        parsed.raw_output = json_result.stdout
        return parsed

    raw_result = get_pr_checks(branch=branch, cwd=repo_path)
    raw_output = raw_result.combined_output

    if raw_output.strip():
        parsed = parse_pr_checks_output(raw_output)
        parsed.raw_output = raw_output
        return parsed

    return CIStatusResult(
        status="unavailable",
        summary="Unable to read GitHub PR checks.",
        raw_output=json_result.combined_output,
        error=json_result.combined_output or raw_result.combined_output,
    )


def apply_ci_status_to_state(
    state: DeliveryState,
    result: CIStatusResult,
) -> None:
    state.ci_status = result.status
    state.ci_summary = result.summary
    state.ci_raw_output = result.raw_output
    state.ci_error = result.error
    state.ci_check_count = len(result.checks)
    state.ci_failed_checks = [
        check.name for check in result.checks if check.status == "failed"
    ]
    state.ci_pending_checks = [
        check.name for check in result.checks if check.status in {"pending", "unknown"}
    ]

    state.mark_completed("check_ci_status")
