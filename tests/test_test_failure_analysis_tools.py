from app.schemas.delivery_state import DeliveryState
from app.tools.test_failure_analysis_tools import (
    classify_test_failure,
    analyze_test_failure,
)


def test_classify_syntax_error():
    output = "SyntaxError: invalid syntax"

    assert classify_test_failure(output) == "syntax_error"


def test_classify_import_error():
    output = "ModuleNotFoundError: No module named 'requests'"

    assert classify_test_failure(output) == "import_error"


def test_classify_attribute_error():
    output = "AttributeError: 'DeliveryState' object has no attribute 'push_branch'"

    assert classify_test_failure(output) == "attribute_error"


def test_classify_assertion_failure():
    output = """
FAILED tests/test_sample.py::test_sample
E   AssertionError: assert 1 == 2
"""

    assert classify_test_failure(output) == "assertion_failure"


def test_analyze_test_failure_from_state():
    state = DeliveryState(
        request_id="req_test",
        repo_path="/tmp/repo",
        original_request="Add test failure analysis",
        test_status="failed",
        test_output="AttributeError: 'DeliveryState' object has no attribute 'push_branch'",
    )

    analysis = analyze_test_failure(state)

    assert analysis.category == "attribute_error"
    assert analysis.likely_causes
    assert analysis.next_actions
    assert analysis.risk_level == "medium"