from pathlib import Path
import subprocess
from app.schemas.delivery_state import DeliveryState
from app.tools.patch_generator_tools import (
    can_generate_readme_patch,
    generate_patch,
)


def test_can_generate_readme_patch():
    state = DeliveryState(
        request_id="req_test",
        repo_path="/tmp/repo",
        original_request="Update README documentation",
    )

    assert can_generate_readme_patch(state) is True


def test_cannot_generate_patch_for_unknown_request():
    state = DeliveryState(
        request_id="req_test",
        repo_path="/tmp/repo",
        original_request="Add payment provider integration",
    )

    assert can_generate_readme_patch(state) is False


def test_generate_readme_patch(tmp_path: Path):
    readme = tmp_path / "README.md"
    readme.write_text("# Test Project\n", encoding="utf-8")
    init_git_repo(tmp_path)
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "chore: initial commit"], cwd=tmp_path, check=True)

    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Update README documentation",
    )

    patch_path = generate_patch(tmp_path, state)

    assert patch_path is not None
    assert patch_path.exists()

    content = patch_path.read_text(encoding="utf-8")

    assert "--- a/README.md" in content
    assert "+++ b/README.md" in content
    assert "DeliveryOps Generated Update" in content


def init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, check=True)


def test_generate_patch_returns_none_for_unsupported_request(tmp_path: Path):
    readme = tmp_path / "README.md"
    readme.write_text("# Test Project\n", encoding="utf-8")

    state = DeliveryState(
        request_id="req_test",
        repo_path=str(tmp_path),
        original_request="Add payment provider integration",
    )

    patch_path = generate_patch(tmp_path, state)

    assert patch_path is None