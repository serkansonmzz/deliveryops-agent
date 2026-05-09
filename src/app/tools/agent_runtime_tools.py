import json
import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from pathlib import Path
from typing import Any

from agno.agent import Agent

from app.agents.base import AgentDefinition


DEFAULT_AGENT_TIMEOUT_SECONDS = 120
DEFAULT_FAST_MODEL = "openai:gpt-5.4-mini"
FAST_AGENT_ROLE_IDS = {
    "intake_agent",
    "product_owner_agent",
    "architecture_council_agent",
    "implementation_planner_agent",
}


def resolve_agent_model(definition: AgentDefinition) -> str:
    if definition.role_id == "dev_agent":
        return os.getenv("DELIVERYOPS_DEV_MODEL") or definition.model

    if definition.role_id in FAST_AGENT_ROLE_IDS:
        return os.getenv("DELIVERYOPS_FAST_MODEL") or DEFAULT_FAST_MODEL

    return os.getenv("DELIVERYOPS_FAST_MODEL") or definition.model


def get_agent_timeout_seconds() -> int:
    raw_value = os.getenv("DELIVERYOPS_AGENT_TIMEOUT_SECONDS")
    if not raw_value:
        return DEFAULT_AGENT_TIMEOUT_SECONDS

    try:
        return max(1, int(raw_value))
    except ValueError:
        return DEFAULT_AGENT_TIMEOUT_SECONDS


def run_agent_with_timeout(
    agent: Agent,
    prompt: str,
    timeout_seconds: int | None = None,
) -> Any:
    timeout = timeout_seconds or get_agent_timeout_seconds()
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(agent.run, prompt)

    try:
        return future.result(timeout=timeout)
    except FutureTimeoutError as exc:
        future.cancel()
        raise TimeoutError(f"Agent call timed out after {timeout} seconds.") from exc
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def append_agent_timing_log(
    repo_path: Path,
    *,
    agent_name: str,
    model: str,
    duration_seconds: float,
    status: str,
    attempt: int | None = None,
    error: str | None = None,
) -> None:
    logs_dir = repo_path / ".deliveryops" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / "agent_timing.json"

    entries: list[dict[str, Any]] = []
    if log_path.exists():
        try:
            existing = json.loads(log_path.read_text(encoding="utf-8"))
            if isinstance(existing, list):
                entries = existing
        except json.JSONDecodeError:
            entries = []

    entry = {
        "agent": agent_name,
        "model": model,
        "duration_seconds": round(duration_seconds, 3),
        "status": status,
    }
    if attempt is not None:
        entry["attempt"] = attempt
    if error:
        entry["error"] = error

    entries.append(entry)
    log_path.write_text(json.dumps(entries, indent=2), encoding="utf-8")
