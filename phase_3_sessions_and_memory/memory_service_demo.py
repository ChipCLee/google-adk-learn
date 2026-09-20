"""
Phase 3: Long-Term Semantic Memory (MemoryService) Demo
Demonstrates:
  - Difference between ephemeral session state and cross-session semantic memory
  - Ingesting episodic facts (user preferences, medical conditions, past events) via ADK MemoryService
  - Querying MemoryService directly via search_memory()
  - Autonomous retrieval in a brand-new session via ADK's preload_memory tool
  - Running live with Google ADK Agent and InMemoryRunner
"""

import asyncio
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.adk.tools import preload_memory
from google.adk.models.lite_llm import LiteLlm
from google.adk.events import Event
from google.genai import types


def create_memory_aware_agent() -> InMemoryRunner:
    """Creates a FitPulse coach agent equipped with ADK long-term memory retrieval."""
    instructions = """
    You are FitPulse, an expert health and wellness coach.
    You have access to the user's long-term memory and history across previous sessions.

    Guidelines:
    1. Always review the user's past memories (injuries, dietary restrictions, workout preferences).
    2. Tailor all advice strictly around past conditions (e.g., avoiding high-impact squats if knee injury, ensuring gluten-free if allergy).
    3. Keep your advice concise, structured, and practical (3-4 bullet points max per section).
    """

    use_gemini = os.getenv("USE_GEMINI", "").lower() in ("1", "true", "yes")
    gemini_key = os.getenv("GEMINI_API_KEY")

    if use_gemini and gemini_key:
        print("[Mode] Google ADK with Cloud Gemini (gemini-2.5-flash)")
        model = "gemini-2.5-flash"
    else:
        ollama_host = os.getenv("OLLAMA_HOST", "http://chips-mac-mini.local:11434")
        api_base = f"{ollama_host}/v1" if not ollama_host.endswith("/v1") else ollama_host
        ollama_model = os.getenv("OLLAMA_MODEL", "openai/gemma4:e4b")
        print(f"[Mode] Google ADK with Ollama ({ollama_model} @ {ollama_host})")

        model = LiteLlm(
            model=ollama_model,
            api_base=api_base,
            api_key="ollama"
        )

    agent = Agent(
        name="fitpulse_memory_coach",
        model=model,
        instruction=instructions,
        tools=[preload_memory]
    )

    return InMemoryRunner(agent=agent, app_name="fitpulse_memory_app")


async def main():
    print("=" * 70)
    print("Phase 3: Long-Term Memory (ADK MemoryService) Demonstration")
    print("=" * 70)

    user_id = "user_alex_101"
    app_name = "fitpulse_memory_app"

    runner = create_memory_aware_agent()

    # Step 1: Ingesting Facts from Past Sessions into ADK MemoryService
    print("\n--- Step 1: Ingesting Facts from Past Sessions (Days/Weeks Ago) ---")
    past_session_events = [
        Event(
            author="user",
            content=types.Content(
                parts=[types.Part.from_text(
                    text="Medical record: User experienced a right meniscus knee tear in 2024; instructed to strictly avoid high-impact squats."
                )]
            )
        ),
        Event(
            author="user",
            content=types.Content(
                parts=[types.Part.from_text(
                    text="Dietary restriction: User has a diagnosed gluten allergy; requires 100% gluten-free meal recommendations."
                )]
            )
        ),
        Event(
            author="user",
            content=types.Content(
                parts=[types.Part.from_text(
                    text="Preference: User prefers morning cardio workouts between 6:30 AM and 7:15 AM."
                )]
            )
        ),
    ]

    await runner.memory_service.add_events_to_memory(
        app_name=app_name,
        user_id=user_id,
        events=past_session_events,
        session_id="session_past_weeks_ago"
    )

    for event in past_session_events:
        text = " ".join([p.text for p in event.content.parts if p.text])
        print(f"  🧠 [ADK MemoryService] Stored: \"{text}\"")

    # Step 2: Direct Semantic / Keyword Search on MemoryService
    print("\n--- Step 2: Querying ADK MemoryService Directly ---")
    search_query = "knee injury and gluten allergy meal"
    print(f"Querying runner.memory_service.search_memory(query=\"{search_query}\")...")
    search_result = await runner.memory_service.search_memory(
        app_name=app_name,
        user_id=user_id,
        query=search_query
    )

    for idx, memory in enumerate(search_result.memories, start=1):
        mem_text = " ".join([p.text for p in memory.content.parts if p.text])
        print(f"  Match #{idx}: {mem_text}")

    # Step 3: Brand New Session (Zero Local Session State)
    new_session_id = "session_new_month_turn_01"
    print("\n--- Step 3: Brand New Session (Zero Ephemeral Session State) ---")
    print(f"Creating clean session '{new_session_id}' with empty session state.")
    await runner.session_service.create_session(
        user_id=user_id,
        session_id=new_session_id,
        app_name=app_name,
        state={}
    )

    user_query = "Can you recommend a leg workout and a post-workout recovery breakfast for me today?"
    print(f"👤 Alex: \"{user_query}\"")

    # Step 4: Live Agent Synthesizes Response Using Preloaded Long-Term Memories
    print("\n--- Step 4: Agent Response (Synthesizing Recalled Long-Term Facts) ---")
    msg = types.Content(role="user", parts=[types.Part.from_text(text=user_query)])

    async for event in runner.run_async(user_id=user_id, session_id=new_session_id, new_message=msg):
        if hasattr(event, "content") and event.content:
            for part in getattr(event.content, "parts", []):
                if getattr(part, "text", None):
                    if not getattr(part, "thought", False):
                        print(part.text, end="", flush=True)

    print("\n\n" + "=" * 70)
    print("Phase 3 MemoryService Demo Complete.")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
