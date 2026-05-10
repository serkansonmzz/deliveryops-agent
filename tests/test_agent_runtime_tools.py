import json
from pathlib import Path
import time

import pytest

from app.agents.base import AgentDefinition
from app.tools.agent_runtime_tools import (
    append_agent_timing_log,
    resolve_agent_model,
    run_agent_with_timeout,
)


class SlowAgent:
    def run(self, prompt: str):
        time.sleep(0.2)
        return prompt


def test_resolve_agent_model_uses_env_overrides(monkeypatch):
    monkeypatch.setenv("DELIVERYOPS_FAST_MODEL", "openai:fast")
    monkeypatch.setenv("DELIVERYOPS_DEV_MODEL", "openai:strong")

    assert (
        resolve_agent_model(
            AgentDefinition(role_id="intake_agent", display_name="Intake", prompt_name="intake")
        )
        == "openai:fast"
    )
    assert (
        resolve_agent_model(
            AgentDefinition(role_id="dev_agent", display_name="Dev", prompt_name="dev_agent")
        )
        == "openai:strong"
    )


def test_resolve_agent_model_uses_fast_default_for_planning_agents(monkeypatch):
    monkeypatch.delenv("DELIVERYOPS_FAST_MODEL", raising=False)

    assert (
        resolve_agent_model(
            AgentDefinition(role_id="implementation_planner_agent", display_name="Planner", prompt_name="implementation_planner")
        )
        == "openai:gpt-5.4-mini"
    )


def test_run_agent_with_timeout_raises_controlled_timeout():
    with pytest.raises(TimeoutError, match="timed out"):
        run_agent_with_timeout(SlowAgent(), "prompt", timeout_seconds=0.01)


def test_append_agent_timing_log(tmp_path: Path):
    append_agent_timing_log(
        tmp_path,
        agent_name="dev_agent",
        model="openai:gpt-5",
        duration_seconds=1.2345,
        status="accepted",
        attempt=1,
    )

    log_path = tmp_path / ".deliveryops" / "logs" / "agent_timing.json"
    data = json.loads(log_path.read_text(encoding="utf-8"))
    assert data[0]["agent"] == "dev_agent"
    assert data[0]["duration_seconds"] == 1.234
    assert data[0]["attempt"] == 1
