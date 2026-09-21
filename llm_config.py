"""Shared Ollama configuration for every phase's LLM-backed examples."""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

try:
    from google.adk.models.lite_llm import LiteLlm
    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False


def model_settings() -> tuple[str, str]:
    """Read the shared model and endpoint; shell variables override .env."""
    model = os.getenv("OLLAMA_MODEL", "ollama/gemma4:e4b")
    host = os.getenv("OLLAMA_HOST", "http://chips-mac-mini.local:11434")
    # LiteLLM's chat provider supports native Ollama tool calls and images.
    if model.startswith("ollama/"):
        model = "ollama_chat/" + model.removeprefix("ollama/")
    elif not model.startswith("ollama_chat/"):
        model = "ollama_chat/" + model
    return model, host


def create_model():
    """Create a fresh ADK model adapter using the project-wide settings."""
    if not ADK_AVAILABLE:
        raise RuntimeError("Live mode requires google-adk and litellm; run uv sync.")
    model, host = model_settings()
    return LiteLlm(model=model, api_base=host)


def model_description() -> str:
    model, host = model_settings()
    return f"{model} @ {host}"


async def run_agent_turn(runner, *, user_id: str, session_id: str, prompt: str) -> dict:
    """Collect a live ADK turn's answer, actual tool calls, and token usage."""
    from google.adk.agents.run_config import RunConfig
    from google.genai import types

    texts, tool_calls, tokens = [], [], 0
    message = types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=message,
        run_config=RunConfig(max_llm_calls=20),
    ):
        if event.error_code:
            raise RuntimeError(f"{event.error_code}: {event.error_message}")
        if event.usage_metadata:
            tokens += event.usage_metadata.total_token_count or 0
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.function_call:
                    tool_calls.append(part.function_call.name)
                if part.text and not part.thought and not event.partial:
                    texts.append(part.text)
    return {"text": "\n".join(texts), "tool_calls": tool_calls, "tokens_used": tokens}


async def ask_agent(*, name: str, instruction: str, prompt: str, tools=None, output_schema=None) -> dict:
    """Run a standalone model-backed node with its own in-memory session."""
    from google.adk.agents import Agent
    from google.adk.runners import InMemoryRunner

    agent = Agent(name=name, model=create_model(), instruction=instruction,
                  tools=tools or [], output_schema=output_schema)
    runner = InMemoryRunner(agent=agent, app_name=name)
    await runner.session_service.create_session(app_name=name, user_id="demo", session_id="demo")
    return await run_agent_turn(runner, user_id="demo", session_id="demo", prompt=prompt)
