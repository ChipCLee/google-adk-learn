import asyncio
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from phase_2_tools_and_actions import cryptocurrency_agent as crypto


def test_agent_registers_remote_mcp_and_shared_model(monkeypatch):
    monkeypatch.setenv("OLLAMA_MODEL", "ollama/gemma4:test")
    monkeypatch.setenv("COINGECKO_MCP_URL", "https://example.test/mcp")
    agent = crypto.create_cryptocurrency_agent()
    assert agent.model.model == "ollama_chat/gemma4:test"
    assert len(agent.tools) == 1
    connection = agent.tools[0]._connection_params
    assert connection.url == "https://example.test/mcp"
    assert connection.terminate_on_close is False


@pytest.mark.parametrize("failure", [None, "discovery", "model"])
def test_runner_closes_mcp_resources_on_success_and_failure(monkeypatch, failure):
    state = {"closed": False, "session_created": False}

    class Toolset:
        async def get_tools(self):
            if failure == "discovery":
                raise ConnectionError("MCP unavailable")
            return [SimpleNamespace(name="execute")]

    class Runner:
        def __init__(self, **kwargs):
            self.session_service = self

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            state["closed"] = True

        async def create_session(self, **kwargs):
            state["session_created"] = True

    async def run_turn(*args, **kwargs):
        if failure == "model":
            raise ConnectionError("Ollama unavailable")
        return {"text": "CoinGecko data", "tool_calls": ["coingecko_execute"]}

    monkeypatch.setattr(crypto, "create_cryptocurrency_agent", lambda: SimpleNamespace(tools=[Toolset()]))
    monkeypatch.setattr("google.adk.runners.InMemoryRunner", Runner)
    monkeypatch.setattr(crypto, "run_agent_turn", run_turn)
    if failure:
        with pytest.raises(ConnectionError):
            asyncio.run(crypto.run("Get Bitcoin price"))
    else:
        asyncio.run(crypto.run("Get Bitcoin price"))
    assert state["closed"]
    assert state["session_created"] is (failure != "discovery")


def test_missing_dependencies_do_not_produce_mock_prices(monkeypatch):
    monkeypatch.setattr(crypto, "ADK_AVAILABLE", False)
    with pytest.raises(RuntimeError, match="uv sync"):
        crypto.create_cryptocurrency_agent()
