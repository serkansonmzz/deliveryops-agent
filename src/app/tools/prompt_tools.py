from pathlib import Path


PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"


def get_prompt_path(prompt_name: str) -> Path:
    normalized = prompt_name.strip()

    if not normalized:
        raise RuntimeError("Prompt name cannot be empty.")

    if "/" in normalized or "\\" in normalized or ".." in normalized:
        raise RuntimeError(f"Unsafe prompt name: {prompt_name}")

    if not normalized.endswith(".md"):
        normalized = f"{normalized}.md"

    return PROMPTS_DIR / normalized


def load_prompt(prompt_name: str) -> str:
    prompt_path = get_prompt_path(prompt_name)

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    content = prompt_path.read_text(encoding="utf-8").strip()

    if not content:
        raise RuntimeError(f"Prompt file is empty: {prompt_path}")

    return content
