import pytest

from app.tools.prompt_tools import get_prompt_path, load_prompt


def test_get_prompt_path_adds_md_extension():
    path = get_prompt_path("dev_agent")

    assert path.name == "dev_agent.md"


def test_get_prompt_path_rejects_unsafe_name():
    with pytest.raises(RuntimeError):
        get_prompt_path("../secrets")


def test_load_prompt_reads_existing_prompt():
    content = load_prompt("dev_agent")

    assert "Dev Agent" in content
    assert "patch" in content.lower()
