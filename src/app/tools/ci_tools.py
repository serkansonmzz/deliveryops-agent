from pathlib import Path

from app.schemas.ci_status import CICheckResult, CIStatusResult
from app.schemas.delivery_state import DeliveryState
from app.tools.git_tools import get_current_branch
from app.tools.github_tools import ensure_gh_authenticated, run_gh


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
    ensure_gh_authenticated()

    branch = state.pr_head_branch or state.pushed_branch or get_current_branch(repo_path)

    if not branch:
        raise RuntimeError("Cannot check CI status because no branch was detected.")

    result = run_gh(
        [
            "pr",
            "checks",
            branch,
        ],
        cwd=repo_path,
    )

    # gh pr checks returns non-zero for failed/pending checks in some cases.
    # We still want to parse the output rather than immediately fail.
    raw_output = "\n".join(
        part for part in [result.stdout, result.stderr] if part.strip()
    )

    if not raw_output.strip():
        if result.return_code != 0:
            raise RuntimeError(result.stderr or "Unable to read GitHub PR checks.")

    return parse_pr_checks_output(raw_output)


def apply_ci_status_to_state(
    state: DeliveryState,
    result: CIStatusResult,
) -> None:
    state.ci_status = result.status
    state.ci_summary = result.summary
    state.ci_raw_output = result.raw_output
    state.ci_check_count = len(result.checks)
    state.ci_failed_checks = [
        check.name for check in result.checks if check.status == "failed"
    ]
    state.ci_pending_checks = [
        check.name for check in result.checks if check.status in {"pending", "unknown"}
    ]

    state.mark_completed("check_ci_status")
