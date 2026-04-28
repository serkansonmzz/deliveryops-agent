import pytest
from app.tools.ci_tools import parse_pr_checks_output


def test_parse_pr_checks_all_passed():
    raw_output = """
check-a (push) success in 1m
check-b (pull_request) success in 2m
"""
    result = parse_pr_checks_output(raw_output)
    assert result.status == "passed"
    assert len(result.checks) == 2
    assert all(c.status == "passed" for c in result.checks)


def test_parse_pr_checks_with_failure():
    raw_output = """
check-a (push) success in 1m
check-b (pull_request) failure in 2m
"""
    result = parse_pr_checks_output(raw_output)
    assert result.status == "failed"
    assert len(result.checks) == 2
    assert result.checks[1].status == "failed"


def test_parse_pr_checks_pending():
    raw_output = """
check-a (push) success in 1m
check-b (pull_request) pending in 2m
"""
    result = parse_pr_checks_output(raw_output)
    assert result.status == "pending"
    assert len(result.checks) == 2
    assert result.checks[1].status == "pending"


def test_parse_pr_checks_no_checks():
    raw_output = ""
    result = parse_pr_checks_output(raw_output)
    assert result.status == "no_checks"
    assert len(result.checks) == 0


def test_parse_pr_checks_cancelled_is_failed():
    raw_output = "check-a (push) cancelled in 1m"
    result = parse_pr_checks_output(raw_output)
    assert result.status == "failed"


def test_parse_pr_checks_queued_is_pending():
    raw_output = "check-a (push) queued in 1m"
    result = parse_pr_checks_output(raw_output)
    assert result.status == "pending"
