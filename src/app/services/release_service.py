from pathlib import Path

from app.services.service_result import ServiceResult
from app.state_store import load_state, save_state
from app.tools.delivery_report_tools import build_final_report, write_final_report
from app.tools.markdown_tracking_tools import update_delivery_markdown
from app.tools.release_candidate_tools import (
    apply_mvp_release_candidate_state,
    write_mvp_release_notes,
)
from app.tools.release_judge_tools import (
    apply_readiness_result_to_state,
    evaluate_release_readiness,
)


def run_readiness_check(repo_path: Path) -> ServiceResult:
    state = load_state(repo_path)

    result = evaluate_release_readiness(repo_path, state)
    apply_readiness_result_to_state(state, result)

    save_state(state)
    update_delivery_markdown(state)

    return ServiceResult(
        status=result.status,
        message=result.summary,
        exit_code=1 if result.status == "blocked" else 0,
        details={
            "risk_level": result.risk_level,
            "blockers": len(result.blockers),
            "warnings": len(result.warnings),
        },
        warnings=result.warnings,
        errors=result.blockers,
    )


def generate_final_report(repo_path: Path) -> ServiceResult:
    state = load_state(repo_path)

    report = build_final_report(state)
    report_path = write_final_report(repo_path, report)

    state.final_report_path = str(report_path.relative_to(repo_path))
    state.final_report_status = "generated"

    state.mark_completed("generate_final_report")

    save_state(state)
    update_delivery_markdown(state)

    return ServiceResult(
        status="generated",
        message="Final report generated.",
        details={"report_path": state.final_report_path},
    )


def generate_mvp_release_notes(repo_path: Path) -> ServiceResult:
    state = load_state(repo_path)

    notes_path = write_mvp_release_notes(repo_path, state)
    apply_mvp_release_candidate_state(state, notes_path, repo_path)

    save_state(state)
    update_delivery_markdown(state)

    return ServiceResult(
        status="generated",
        message="MVP release notes generated.",
        details={"release_notes": state.mvp_release_notes_path},
    )
