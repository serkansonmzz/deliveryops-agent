from pathlib import Path

from app.tools.smoke_test_tools import run_local_smoke_test


def test_run_local_smoke_test(tmp_path: Path):
    result = run_local_smoke_test(tmp_path / "smoke")

    assert result.passed is True
    assert result.commit_hash
    assert result.pushed is True
    assert result.branch_name == "feature/smoke-e2e"

    final_report_path = Path(result.final_report_path)

    assert final_report_path.exists()
    assert "DeliveryOps Final Report" in final_report_path.read_text(encoding="utf-8")