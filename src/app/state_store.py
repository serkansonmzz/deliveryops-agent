import json
from pathlib import Path
from app.schemas.delivery_state import DeliveryState, utc_now_iso


STATE_FILE_NAME = "state.json"


def ensure_workspace(repo_path: Path) -> Path:
    workspace = repo_path / ".deliveryops"
    logs = workspace / "logs"

    workspace.mkdir(exist_ok=True)
    logs.mkdir(exist_ok=True)

    return workspace


def save_state(state: DeliveryState) -> Path:
    workspace = ensure_workspace(Path(state.repo_path))
    state.updated_at = utc_now_iso()

    state_path = workspace / STATE_FILE_NAME
    state_path.write_text(
        json.dumps(state.model_dump(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return state_path


def load_state(repo_path: Path) -> DeliveryState:
    state_path = repo_path / ".deliveryops" / STATE_FILE_NAME

    if not state_path.exists():
        raise FileNotFoundError(f"State file not found: {state_path}")

    data = json.loads(state_path.read_text(encoding="utf-8"))
    return DeliveryState(**data)