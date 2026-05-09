from pathlib import Path

from app.services.service_result import ServiceResult
from app.state_store import load_state, save_state
from app.tools.markdown_tracking_tools import update_delivery_markdown
from app.tools.test_failure_analysis_tools import analyze_test_failure
from app.tools.test_tools import detect_test_command, run_safe_test_command


def detect_tests(repo_path: Path) -> ServiceResult:
    state = load_state(repo_path)

    command = detect_test_command(repo_path)

    if command is None:
        state.test_status = "not_detected"
        state.test_command = None
        state.test_summary = "No known test command was detected."
        state.mark_completed("detect_tests")

        save_state(state)
        update_delivery_markdown(state)

        return ServiceResult(
            status="not_detected",
            message="No test command detected.",
            details={"test_status": state.test_status},
        )

    state.test_command = command
    state.test_status = "detected"
    state.test_summary = f"Detected test command: {command}"
    state.mark_completed("detect_tests")

    save_state(state)
    update_delivery_markdown(state)

    return ServiceResult(
        status="detected",
        message="Test command detected.",
        details={
            "command": command,
            "test_status": state.test_status,
        },
    )


def run_tests(repo_path: Path) -> ServiceResult:
    state = load_state(repo_path)

    if not state.test_command:
        detected = detect_test_command(repo_path)

        if not detected:
            state.test_status = "not_detected"
            state.test_summary = "No known test command was detected."
            state.mark_completed("detect_tests")

            save_state(state)
            update_delivery_markdown(state)

            return ServiceResult(
                status="not_detected",
                message="No test command detected.",
                details={"test_status": state.test_status},
            )

        state.test_command = detected
        state.mark_completed("detect_tests")

    result = run_safe_test_command(repo_path, state.test_command)

    state.test_status = result.status
    state.test_exit_code = result.exit_code
    state.test_output = "\n".join(
        part for part in [result.stdout, result.stderr] if part.strip()
    )
    state.test_summary = result.summary
    state.mark_completed("run_tests")

    if result.status == "passed":
        state.test_failure_category = None
        state.test_failure_analysis_summary = None
        state.test_failure_likely_causes = []
        state.test_failure_next_actions = []
        state.test_failure_risk_level = None

    save_state(state)
    update_delivery_markdown(state)

    return ServiceResult(
        status=result.status,
        message="Tests passed." if result.status == "passed" else "Tests failed.",
        exit_code=0 if result.status == "passed" else 1,
        details={
            "command": result.command,
            "exit_code": result.exit_code,
            "test_status": result.status,
        },
    )


def analyze_failed_tests(repo_path: Path) -> ServiceResult:
    state = load_state(repo_path)

    if state.test_status != "failed":
        return ServiceResult(
            status="skipped",
            message="No failed test run found.",
            exit_code=0,
        )

    analysis = analyze_test_failure(state)

    state.test_failure_category = analysis.category
    state.test_failure_analysis_summary = analysis.summary
    state.test_failure_likely_causes = analysis.likely_causes
    state.test_failure_next_actions = analysis.next_actions
    state.test_failure_risk_level = analysis.risk_level

    state.mark_completed("analyze_test_failure")

    save_state(state)
    update_delivery_markdown(state)

    return ServiceResult(
        status="analyzed",
        message="Test failure analyzed.",
        details={
            "category": analysis.category,
            "risk_level": analysis.risk_level,
        },
    )
