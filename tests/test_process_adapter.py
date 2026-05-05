from app.adapters.process_adapter import run_process, run_process_or_raise
import pytest


def test_run_process_success(tmp_path):
    result = run_process(["python", "-c", "print('hello')"], cwd=tmp_path)

    assert result.ok is True
    assert result.return_code == 0
    assert "hello" in result.stdout


def test_run_process_or_raise_raises_on_failure(tmp_path):
    with pytest.raises(RuntimeError):
        run_process_or_raise(
            ["python", "-c", "import sys; sys.exit(2)"],
            cwd=tmp_path,
        )
