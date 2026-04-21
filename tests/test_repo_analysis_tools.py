from pathlib import Path

from app.tools.repo_analysis_tools import (
    detect_project_stack,
    find_likely_files,
    list_repo_files,
)


def test_detect_project_stack_python(tmp_path: Path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='test'\n")

    stack = detect_project_stack(tmp_path)

    assert "python" in stack


def test_list_repo_files_ignores_git_and_deliveryops(tmp_path: Path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")
    (tmp_path / ".deliveryops").mkdir()
    (tmp_path / ".deliveryops" / "state.json").write_text("{}")

    files = list_repo_files(tmp_path)

    assert "src/main.py" in files
    assert ".deliveryops/state.json" not in files


def test_find_likely_files_for_branch_request(tmp_path: Path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app").mkdir()
    (tmp_path / "src" / "app" / "tools").mkdir(parents=True, exist_ok=True)
    (tmp_path / "src" / "app" / "tools" / "branch_name_tools.py").write_text("")
    (tmp_path / "src" / "app" / "tools" / "git_tools.py").write_text("")

    files = find_likely_files(tmp_path, "Add branch creation")

    assert "src/app/tools/branch_name_tools.py" in files