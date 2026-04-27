from app.schemas.delivery_state import DeliveryState
from app.schemas.test_failure_analysis import TestFailureAnalysis


def normalize_output(text: str | None, max_chars: int = 12000) -> str:
    if not text:
        return ""

    return text[-max_chars:]


def classify_test_failure(output: str) -> str:
    lowered = output.lower()

    if "syntaxerror" in lowered or "indentationerror" in lowered:
        return "syntax_error"

    if "modulenotfounderror" in lowered or "importerror" in lowered:
        return "import_error"

    if "attributeerror" in lowered:
        return "attribute_error"

    if "typeerror" in lowered:
        return "type_error"

    if "assertionerror" in lowered or "assert " in lowered:
        return "assertion_failure"

    if "command not found" in lowered or "no such file or directory" in lowered:
        return "environment_error"

    if "failed" in lowered and "passed" in lowered:
        return "test_assertion_or_regression"

    if "timeout" in lowered or "timed out" in lowered:
        return "timeout"

    return "unknown_failure"


def build_likely_causes(category: str) -> list[str]:
    if category == "syntax_error":
        return [
            "A Python syntax or indentation issue was introduced.",
            "A generated or edited file may contain malformed code.",
            "Check the exact file and line number in the test output.",
        ]

    if category == "import_error":
        return [
            "A module import path may be wrong.",
            "A new dependency may be missing from pyproject.toml.",
            "A file may have been created in the wrong package location.",
        ]

    if category == "attribute_error":
        return [
            "Code may reference a field or function that does not exist.",
            "A schema field name may not match the code using it.",
            "A previous rename may not have been applied everywhere.",
        ]

    if category == "type_error":
        return [
            "A function may be called with the wrong arguments.",
            "A return type may not match what the caller expects.",
            "A Pydantic model or tool function contract may have changed.",
        ]

    if category == "assertion_failure":
        return [
            "The implementation behavior does not match the test expectation.",
            "The test expectation may need updating if the behavior intentionally changed.",
            "Inspect the failing assertion and compare it with the feature request.",
        ]

    if category == "environment_error":
        return [
            "The test command may require a missing binary or dependency.",
            "The local environment may not be initialized correctly.",
            "The command may be safe but unavailable in this repository.",
        ]

    if category == "timeout":
        return [
            "The test command may be hanging.",
            "A test may wait on network, IO, or an interactive prompt.",
            "The timeout may be too low for this project.",
        ]

    return [
        "The failure type could not be classified confidently.",
        "Inspect the last test output lines manually.",
        "Check recent changes and compare them with failing tests.",
    ]


def build_next_actions(category: str) -> list[str]:
    common = [
        "Do not commit, push, or open a PR until the test failure is resolved.",
        "Inspect DELIVERY.md and the test output before changing code.",
    ]

    if category == "syntax_error":
        return [
            "Open the file and line reported by the test output.",
            "Fix the syntax or indentation issue.",
            "Run `uv run deliveryops run-tests --repo .` again.",
            *common,
        ]

    if category == "import_error":
        return [
            "Check whether the imported module exists.",
            "Verify package paths and `__init__.py` files.",
            "Add missing dependency only if it is truly required.",
            "Run tests again after the import fix.",
            *common,
        ]

    if category == "attribute_error":
        return [
            "Search for the missing attribute name across the codebase.",
            "Align schema field names and usage sites.",
            "Run targeted tests first, then the full safe test command.",
            *common,
        ]

    if category == "type_error":
        return [
            "Inspect the failing function call and expected signature.",
            "Update the caller or callee so the contract matches.",
            "Run tests again after the contract fix.",
            *common,
        ]

    if category == "assertion_failure":
        return [
            "Read the failing assertion carefully.",
            "Decide whether the implementation is wrong or the test expectation is outdated.",
            "Prefer fixing implementation unless the requested behavior changed intentionally.",
            "Run tests again after the fix.",
            *common,
        ]

    if category == "environment_error":
        return [
            "Verify the test command exists in this environment.",
            "Install missing dev dependencies through the project package manager, not system Python.",
            "Re-run test detection if the test setup changed.",
            *common,
        ]

    if category == "timeout":
        return [
            "Find which test is hanging.",
            "Check for accidental network calls, sleeps, or interactive prompts.",
            "Consider running a narrower test command manually.",
            *common,
        ]

    return [
        "Read the last output lines in DELIVERY.md.",
        "Inspect changed files from the current workflow.",
        "Run a narrower test if possible.",
        *common,
    ]


def summarize_failure(category: str, output: str) -> str:
    if not output.strip():
        return "Tests failed, but no output was captured."

    lines = output.splitlines()
    tail = "\n".join(lines[-12:])

    return (
        f"Test failure category: `{category}`.\n\n"
        f"Last relevant output lines:\n\n"
        f"```text\n{tail}\n```"
    )


def analyze_test_failure(state: DeliveryState) -> TestFailureAnalysis:
    output = normalize_output(state.test_output or state.test_summary)

    category = classify_test_failure(output)

    return TestFailureAnalysis(
        category=category,
        summary=summarize_failure(category, output),
        likely_causes=build_likely_causes(category),
        next_actions=build_next_actions(category),
        risk_level="high" if category in {"syntax_error", "import_error", "timeout"} else "medium",
    )