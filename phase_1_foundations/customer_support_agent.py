"""
Phase 1: Customer Support Triage & FAQ Agent
Demonstrates:
  - Agent initialization with system instructions and model configuration
  - Running via InMemoryRunner
  - Asynchronous event streaming with run_async()
  - Multi-turn conversation handling
  - Sending a camera image with a text question
"""

import asyncio
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Attempt to import from google.adk; provide a self-contained fallback for offline learning
try:
    from google.adk.agents import Agent
    from google.adk.agents.run_config import RunConfig, StreamingMode
    from google.adk.runners import InMemoryRunner
    from google.adk.models.lite_llm import LiteLlm
    from google.genai import types
    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False


# =====================================================================
# Simulation / Fallback Components (Used when google-adk is not installed)
# =====================================================================
class MockEvent:
    def __init__(self, content: str, event_type: str = "model_response"):
        self.content = content
        self.event_type = event_type

    def __repr__(self):
        return f"<Event type={self.event_type} content={self.content[:40]}...>"


class MockAgent:
    def __init__(self, name: str, model: str, instruction: str):
        self.name = name
        self.model = model
        self.instruction = instruction


class MockInMemoryRunner:
    def __init__(self, agent, app_name: str = "support_app"):
        self.agent = agent
        self.app_name = app_name
        self.sessions = {}

    async def run_async(self, user_id: str, session_id: str, new_message: str):
        # Track history
        key = (user_id, session_id)
        if key not in self.sessions:
            self.sessions[key] = []
        self.sessions[key].append({"role": "user", "content": new_message})

        # Yield a mock response illustrating what Gemini would generate
        yield MockEvent("Analyzing customer request and determining category...", "thought")
        await asyncio.sleep(0.3)

        msg_lower = new_message.lower() if isinstance(new_message, str) else ""
        if "charge" in msg_lower or "bill" in msg_lower or "invoice" in msg_lower:
            category = "[Category: Billing & Invoices]"
            response = (
                f"{category}\nHello! I understand you have a question regarding a recent charge on your invoice. "
                "I can certainly help you review your billing details. Could you please provide your Account ID or Invoice Number so I can locate the transaction?"
            )
        elif "rate limit" in msg_lower or "api" in msg_lower or "error" in msg_lower:
            category = "[Category: Technical Support]"
            response = (
                f"{category}\nI'm sorry to hear you're experiencing technical difficulties. "
                "Could you please share the error code or API endpoint that is failing, along with any HTTP status codes you received?"
            )
        else:
            category = "[Category: General Inquiry]"
            response = (
                f"{category}\nThank you for reaching out to CloudScale Systems! How may I assist you today?"
            )

        self.sessions[key].append({"role": "agent", "content": response})
        yield MockEvent(response, "content")


# =====================================================================
# Real Agent Definition & Factory
# =====================================================================
def create_customer_support_agent():
    """Defines the Tier-1 Customer Support Triage Agent."""
    instructions = """
    You are an intelligent Tier-1 Customer Support Triage Agent for CloudScale Systems.
    Your responsibilities:
    1. Always begin your response with the category tag:
       - [Billing & Invoices]
       - [Technical Support]
       - [Account Access]
       - [General Inquiry]
    2. Be extremely concise and direct (2 to 3 short sentences maximum).
    3. Ask at most 1-2 essential clarifying questions if details are missing.
    """

    if ADK_AVAILABLE:
        # Use local Ollama on Mac Mini with Gemma 4 E4B by default
        ollama_host = os.getenv("OLLAMA_HOST", "http://chips-mac-mini.local:11434")
        ollama_model = os.getenv("OLLAMA_MODEL", "ollama/gemma4:e4b")
        print(f"[Mode] Live Google ADK with Ollama ({ollama_model} @ {ollama_host})")

        model_backend = LiteLlm(
            model=ollama_model,
            api_base=ollama_host
        )

        agent = Agent(
            name="cloudscale_support_agent",
            model=model_backend,
            instruction=instructions
        )
        runner = InMemoryRunner(agent=agent, app_name="cloudscale_support")
        return runner

    else:
        print("[Notice] google-adk not installed; using built-in Simulation Mode.")
        agent = MockAgent(
            name="cloudscale_support_agent",
            model="gemma4:e4b",
            instruction=instructions
        )
        runner = MockInMemoryRunner(agent=agent, app_name="cloudscale_support")
        return runner



async def main():
    print("=" * 70)
    print("Phase 1: Customer Support Triage Agent Demo")
    print("=" * 70)

    runner = create_customer_support_agent()
    user_id = "user_corp_892"
    session_id = "session_turn_001"

    if ADK_AVAILABLE and hasattr(runner, "session_service"):
        try:
            await runner.session_service.create_session(user_id=user_id, session_id=session_id, app_name="cloudscale_support")
        except Exception:
            pass


    # Each turn contains text and, optionally, a local image attachment.
    conversation_turns = [
        {"text": "Hi, I noticed an unexpected charge of $149 on my monthly invoice for compute services."},
        {"text": "My Account ID is CS-88219, and the invoice number is INV-2026-09."},
        {"text": "Thank you! Could you also check if our API rate limits were exceeded yesterday?"},
        {
            "text": (
                "Explain what is visible in this image, including the setting, "
                "people, and objects. Describe only details you can see."
            ),
            "image_path": Path(__file__).resolve().parent.parent
            / "artifacts" / "camera-20260920-140535.jpg",
        },
    ]

    try:
        for turn_idx, turn in enumerate(conversation_turns, start=1):
            user_input = turn["text"]
            image_path = turn.get("image_path")
            print(f"\n--- Turn {turn_idx} ---")
            print(f"👤 User: {user_input}")
            if image_path is not None:
                print(f"📷 Image: {image_path}")
                if not ADK_AVAILABLE:
                    print("[Notice] Image analysis requires live ADK; skipping this turn in simulation mode.")
                    continue

            if ADK_AVAILABLE:
                parts = [types.Part.from_text(text=user_input)]
                if image_path is not None:
                    parts.append(types.Part.from_bytes(
                        data=image_path.read_bytes(),
                        mime_type="image/jpeg",
                    ))
                msg = types.Content(role="user", parts=parts)
            else:
                msg = user_input

            print("🤖 Agent Response:")
            run_options = (
                {"run_config": RunConfig(streaming_mode=StreamingMode.SSE)}
                if ADK_AVAILABLE else {}
            )

            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=msg,
                **run_options,
            ):
                if hasattr(event, "content") and event.content:
                    if hasattr(event.content, "parts") and event.content.parts:
                        # ADK also emits a final combined response; skip it to
                        # avoid printing the streamed text a second time.
                        if not event.partial:
                            continue
                        for part in event.content.parts:
                            if part.text and not part.thought:
                                print(part.text, end="", flush=True)
                    elif isinstance(event.content, str):
                        print(f"  {event.content}")
            if ADK_AVAILABLE:
                print()
    except Exception as e:
        if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
            print(f"\n⚠️ [Notice] Gemini Free Tier rate limit reached (5 requests/min). Displaying simulated responses.")
        else:
            raise e



if __name__ == "__main__":
    asyncio.run(main())
