from pathlib import Path

from app.tools.repo_analysis_tools import (
    analyze_repository,
    build_source_test_map,
    classify_files,
    detect_risky_files,
    detect_stack_from_files,
    list_repo_files,
    rank_likely_files,
)


def test_detect_stack_from_python_uv_files():
    files = [
        "pyproject.toml",
        "uv.lock",
        "src/app/main.py",
        "tests/test_main.py",
    ]

    stack = detect_stack_from_files(files)

    assert "python" in stack
    assert "uv" in stack


def test_classify_files():
    files = [
        "src/app/main.py",
        "tests/test_main.py",
        "README.md",
        "pyproject.toml",
        ".github/workflows/ci.yml",
    ]

    source_files, test_files, documentation_files, config_files = classify_files(files)

    assert "src/app/main.py" in source_files
    assert "tests/test_main.py" in test_files
    assert "README.md" in documentation_files
    assert "pyproject.toml" in config_files
    assert ".github/workflows/ci.yml" in config_files


def test_list_repo_files_ignores_git_and_deliveryops(tmp_path: Path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')\n", encoding="utf-8")
    (tmp_path / ".deliveryops").mkdir()
    (tmp_path / ".deliveryops" / "state.json").write_text("{}", encoding="utf-8")

    files = list_repo_files(tmp_path)

    assert "src/main.py" in files
    assert ".deliveryops/state.json" not in files


def test_detect_risky_files():
    files = [
        ".env.example",
        "src/app/main.py",
        ".github/workflows/ci.yml",
        "deploy/prod.yml",
    ]

    risky = detect_risky_files(files)

    assert ".env.example" in risky
    assert ".github/workflows/ci.yml" in risky
    assert "deploy/prod.yml" in risky


def test_detect_risky_files_flags_runtime_cache_files():
    files = [
        ".DS_Store",
        "src/app/__pycache__/main.cpython-312.pyc",
        "src/app/main.py",
    ]

    risky = detect_risky_files(files)

    assert ".DS_Store" in risky
    assert "src/app/__pycache__/main.cpython-312.pyc" in risky


def test_rank_likely_files_for_readme_request():
    files = [
        "README.md",
        "src/app/main.py",
        "docs/WORKFLOW_OVERVIEW.md",
    ]

    likely = rank_likely_files(files, "Update README documentation")

    assert likely
    assert likely[0].path == "README.md"


def test_build_source_test_map_matches_python_test_file():
    source_files = ["src/app/tools/test_tools.py"]
    test_files = ["tests/test_test_tools.py"]

    mapping = build_source_test_map(source_files, test_files)

    assert mapping["src/app/tools/test_tools.py"] == ["tests/test_test_tools.py"]


def test_analyze_repository_counts_files(tmp_path: Path):
    (tmp_path / "src" / "app").mkdir(parents=True)
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / "app" / "main.py").write_text(
        "print('hi')\n",
        encoding="utf-8",
    )
    (tmp_path / "tests" / "test_main.py").write_text(
        "def test_x(): assert True\n",
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname='x'\n",
        encoding="utf-8",
    )

    result = analyze_repository(tmp_path, "Update README")

    assert "python" in result.detected_stack
    assert result.source_files
    assert result.test_files
    assert result.documentation_files
    assert result.likely_files
