"""
Phase 4: Autonomous Multi-Agent Software Engineering Team
Demonstrates:
  - Real Google ADK Multi-Agent Orchestration with specialized sub-agents
  - Single-turn sub-agents (mode='single_turn') exposed automatically as callable tools
  - Hierarchical coordination via Lead Architect Agent
  - Real LLM generation for Backend, Frontend, and QA deliverables (Gemma 4 on Mac Mini / Gemini)
"""

import asyncio
import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.adk.models.lite_llm import LiteLlm
from google.genai import types


def create_software_team() -> InMemoryRunner:
    """Creates a multi-agent engineering team led by a Solutions Architect."""
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

    # 1. Specialized Backend Engineer (FastAPI, schemas, endpoints)
    backend_engineer = Agent(
        name="backend_engineer",
        description="Senior backend engineer specializing in FastAPI endpoints, Pydantic schemas, and database operations.",
        model=model,
        instruction="""
        You are a senior backend engineer specializing in FastAPI and Pydantic.
        When asked to design a backend feature, generate:
        1. Concise FastAPI endpoint signatures (HTTP method, path, status code).
        2. Pydantic request and response schema models.
        Be concise, professional, and practical (2-3 code blocks maximum).
        """,
        mode="single_turn"
    )

    # 2. Specialized Frontend Engineer (React, TypeScript, UI state)
    frontend_engineer = Agent(
        name="frontend_engineer",
        description="Senior frontend engineer specializing in React, TypeScript, and state management.",
        model=model,
        instruction="""
        You are a senior frontend engineer specializing in React and TypeScript.
        When asked to design a frontend component, generate:
        1. A clean React component structure using hooks (useState, form submission).
        2. TypeScript interfaces for component props and state.
        Be concise, modular, and modern (2-3 code blocks maximum).
        """,
        mode="single_turn"
    )

    # 3. Specialized QA & Security Engineer (Pytest, security audits)
    qa_engineer = Agent(
        name="qa_engineer",
        description="Senior QA and security engineer specializing in automated test suites and security audits.",
        model=model,
        instruction="""
        You are a senior QA & application security engineer.
        When asked to review a feature, generate:
        1. A concise pytest test suite covering happy-path and failure scenarios.
        2. A security checklist highlighting potential vulnerabilities (e.g. rate limiting, auth token handling, input sanitization).
        Be concise and thorough.
        """,
        mode="single_turn"
    )

    # 4. Lead Solutions Architect (Hierarchical Coordinator)
    lead_architect = Agent(
        name="lead_architect",
        model=model,
        instruction="""
        You are the Lead Solutions Architect for a high-performance software engineering team.
        When given a software feature request:
        1. Coordinate with your engineering team by delegating to:
           - `backend_engineer`: for API design and Pydantic schemas
           - `frontend_engineer`: for React UI components and state hooks
           - `qa_engineer`: for pytest test suites and security auditing
        2. Review their deliverables and synthesize them into an executive engineering delivery report with:
           - Architecture Overview
           - Backend Deliverables
           - Frontend Deliverables
           - QA & Security Summary
        Keep your synthesis sharp, technical, and well-structured.
        """,
        sub_agents=[backend_engineer, frontend_engineer, qa_engineer]
    )

    return InMemoryRunner(agent=lead_architect, app_name="software_team_app")


# =====================================================================
# Main Execution
# =====================================================================
async def main():
    print("=" * 70)
    print("Phase 4: Autonomous Multi-Agent Software Engineering Team")
    print("=" * 70)

    runner = create_software_team()
    user_id = "user_lead_architect_01"
    session_id = "session_feature_sprint_01"

    await runner.session_service.create_session(
        user_id=user_id,
        session_id=session_id,
        app_name="software_team_app"
    )

    feature_request = "Build a secure user authentication system with JWT tokens, a login UI, and automated security tests."
    print(f"\n📋 [Feature Request]: \"{feature_request}\"")
    print("\n🚀 [Lead Architect] Mobilizing specialized sub-agents...\n")

    msg = types.Content(role="user", parts=[types.Part.from_text(text=feature_request)])

    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=msg):
        if hasattr(event, "content") and event.content:
            for part in getattr(event.content, "parts", []):
                # Sub-agent tool delegation event
                if getattr(part, "function_call", None):
                    call = part.function_call
                    print(f"\n⚙️  [Lead Architect] Delegating to Sub-Agent: '{call.name}'")
                # Sub-agent response output
                elif getattr(part, "function_response", None):
                    res = part.function_response
                    print(f"📥 [Deliverable Received] from '{res.name}'")
                # Synthesized or verbal agent text
                elif getattr(part, "text", None) and not getattr(part, "thought", False):
                    author = getattr(event, "author", "Agent")
                    print(f"\n🗣️  [{author}]:\n{part.text.strip()}\n")

    print("=" * 70)
    print("Phase 4 Autonomous Multi-Agent Team Demo Complete.")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
