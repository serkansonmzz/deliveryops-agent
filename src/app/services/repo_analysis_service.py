from pathlib import Path

from app.services.service_result import ServiceResult
from app.state_store import load_state, save_state
from app.tools.markdown_tracking_tools import update_delivery_markdown
from app.tools.repo_analysis_tools import analyze_repository


def run_repo_analysis(repo_path: Path) -> ServiceResult:
    state = load_state(repo_path)
    result = analyze_repository(repo_path, state.original_request)

    state.detected_stack = result.detected_stack
    state.repo_analysis_summary = result.summary
    state.repo_source_file_count = len(result.source_files)
    state.repo_test_file_count = len(result.test_files)
    state.repo_documentation_file_count = len(result.documentation_files)
    state.repo_config_file_count = len(result.config_files)
    state.repo_risky_files = result.risky_files
    state.repo_source_test_map = result.source_test_map

    if result.likely_files:
        state.likely_files = [item.path for item in result.likely_files]

    state.mark_completed("analyze_repository")

    save_state(state)
    update_delivery_markdown(state)

    return ServiceResult(
        status="analyzed",
        message=result.summary,
        details={
            "source_files": len(result.source_files),
            "test_files": len(result.test_files),
            "documentation_files": len(result.documentation_files),
            "config_files": len(result.config_files),
            "likely_files": len(result.likely_files),
            "risky_files": len(result.risky_files),
        },
        warnings=[
            f"Risky file detected: {file_path}"
            for file_path in result.risky_files[:10]
        ],
    )
