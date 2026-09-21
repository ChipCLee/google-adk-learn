import asyncio
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import llm_config


@pytest.mark.parametrize("configured", [
    "gemma4:26b", "ollama/gemma4:26b", "ollama_chat/gemma4:26b",
])
def test_model_uses_configured_host_and_chat_provider(monkeypatch, configured):
    monkeypatch.setenv("OLLAMA_MODEL", configured)
    monkeypatch.setenv("OLLAMA_HOST", "http://test-server:11434")
    monkeypatch.setattr(llm_config, "ADK_AVAILABLE", True)
    monkeypatch.setattr(llm_config, "LiteLlm", lambda **kwargs: kwargs)
    assert llm_config.create_model() == {
        "model": "ollama_chat/gemma4:26b", "api_base": "http://test-server:11434",
    }


def test_dotenv_is_loaded_relative_to_config_not_working_directory(tmp_path):
    # Use a separate config/.env pair to avoid reading or modifying real secrets.
    module = tmp_path / "llm_config.py"
    module.write_text(Path(llm_config.__file__).read_text())
    (tmp_path / ".env").write_text(
        "OLLAMA_HOST=http://dotenv-server:11434\nOLLAMA_MODEL=gemma4:test\n"
    )
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    env = os.environ.copy()
    for key in ("OLLAMA_HOST", "OLLAMA_MODEL", "GEMINI_API_KEY", "GOOGLE_API_KEY"):
        env.pop(key, None)
    env["PYTHONPATH"] = str(tmp_path)
    result = subprocess.run(
        [sys.executable, "-c", "import llm_config; print(llm_config.model_settings())"],
        cwd=elsewhere, env=env, text=True, capture_output=True, check=True,
    )
    assert "ollama_chat/gemma4:test" in result.stdout
    assert "http://dotenv-server:11434" in result.stdout


def test_tool_state_mutations_are_recorded_in_adk_delta():
    from google.adk.sessions.state import State
    from phase_2_tools_and_actions.financial_research_agent import manage_watchlist
    from phase_3_sessions_and_memory.wellness_coach_agent import log_meal, log_workout

    initial = {"watchlist": ["GOOGL"], "logged_meals": [], "logged_workouts": []}
    delta = {}
    context = SimpleNamespace(state=State(initial, delta))
    manage_watchlist("add", "AAPL", context)
    log_meal("Oatmeal", 380, context)
    log_workout("running", 30, context)
    assert delta["watchlist"] == ["GOOGL", "AAPL"]
    assert delta["calories_consumed"] == 380
    assert delta["calories_burned"] == 330
    assert len(delta["logged_meals"]) == len(delta["logged_workouts"]) == 1


def test_live_result_uses_actual_tool_calls_and_usage():
    from google.genai import types

    def event(parts, tokens=0):
        return SimpleNamespace(
            content=types.Content(role="model", parts=parts),
            usage_metadata=SimpleNamespace(total_token_count=tokens),
            partial=False, error_code=None,
        )

    class Runner:
        async def run_async(self, **kwargs):
            assert kwargs["new_message"].parts[0].text == "Check this sample"
            yield event([types.Part(text="Internal reasoning", thought=True)])
            yield event([types.Part.from_function_call(name="verify_governing_law", args={})], 12)
            yield event([types.Part.from_text(text="Approved")], 8)

    result = asyncio.run(llm_config.run_agent_turn(
        Runner(), user_id="test", session_id="test", prompt="Check this sample",
    ))
    assert result == {"text": "Approved", "tool_calls": ["verify_governing_law"], "tokens_used": 20}


def test_phase_one_missing_optional_image_keeps_text_demo_working(monkeypatch, capsys):
    from google.genai import types
    from phase_1_foundations import customer_support_agent as demo

    calls = []

    class Runner:
        async def run_async(self, **kwargs):
            calls.append(kwargs["new_message"])
            yield SimpleNamespace(partial=True, content=types.Content(
                role="model", parts=[types.Part.from_text(text="Test response")],
            ))

    monkeypatch.setattr(demo, "create_customer_support_agent", Runner)
    monkeypatch.setattr(demo, "ADK_AVAILABLE", True)
    monkeypatch.setattr(Path, "is_file", lambda self: False)
    asyncio.run(demo.main())
    assert len(calls) == 3
    assert "Saved camera image is missing" in capsys.readouterr().out
