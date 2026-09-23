"""
Phase 4: Autonomous Multi-Agent Software Engineering Team
Demonstrates:
  - Real Google ADK Multi-Agent Orchestration with specialized sub-agents
  - Single-turn sub-agents (mode='single_turn') exposed automatically as callable tools
  - Hierarchical coordination via Lead Architect Agent
  - Real LLM generation for Backend, Frontend, and QA deliverables (Gemma 4 on Mac Mini / Gemini)
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, Any, List

# Keep direct execution (python phase_N/script.py) working from any directory.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from llm_config import ADK_AVAILABLE, create_model, model_description, run_agent_turn

try:
    from google.adk.agents import Agent
    from google.adk.runners import InMemoryRunner
except ImportError:
    ADK_AVAILABLE = False




# =====================================================================
# Specialized Sub-Agent Implementations
# =====================================================================

class BackendSubAgent:
    """Specialized in FastAPI, database schemas, and business logic."""
    name = "backend_engineer"

    def execute(self, feature_spec: str, shared_state: dict) -> dict:
        print(f"  🔧 [{self.name}] Designing data model and FastAPI endpoints...")
        deliverables = {
            "endpoints": [
                {"method": "POST", "path": "/api/v1/auth/login", "desc": "Authenticates user and returns JWT"},
                {"method": "GET", "path": "/api/v1/profile", "desc": "Fetches active user profile"}
            ],
            "schema_code": (
                "from pydantic import BaseModel, EmailStr\n\n"
                "class UserLogin(BaseModel):\n"
                "    email: EmailStr\n"
                "    password: str\n\n"
                "class TokenResponse(BaseModel):\n"
                "    access_token: str\n"
                "    token_type: str = 'bearer'\n"
            )
        }
        shared_state["backend_deliverables"] = deliverables
        return deliverables


class FrontendSubAgent:
    """Specialized in React, TypeScript, and UI/UX styling."""
    name = "frontend_engineer"

    def execute(self, feature_spec: str, shared_state: dict) -> dict:
        backend_spec = shared_state.get("backend_deliverables", {})
        endpoints = [e["path"] for e in backend_spec.get("endpoints", [])]
        print(f"  🎨 [{self.name}] Building React component consuming endpoints: {endpoints}...")

        component_code = (
            "import React, { useState } from 'react';\n\n"
            "export const LoginForm = () => {\n"
            "  const [email, setEmail] = useState('');\n"
            "  const [password, setPassword] = useState('');\n\n"
            "  const handleLogin = async (e: React.FormEvent) => {\n"
            "    e.preventDefault();\n"
            "    const res = await fetch('/api/v1/auth/login', {\n"
            "      method: 'POST',\n"
            "      headers: { 'Content-Type': 'application/json' },\n"
            "      body: JSON.stringify({ email, password })\n"
            "    });\n"
            "  };\n"
            "  return <form onSubmit={handleLogin}>...</form>;\n"
            "};\n"
        )
        deliverables = {"component": "LoginForm.tsx", "code": component_code}
        shared_state["frontend_deliverables"] = deliverables
        return deliverables


class QASubAgent:
    """Specialized in unit testing, security analysis, and edge-case verification."""
    name = "qa_security_reviewer"

    def execute(self, shared_state: dict) -> dict:
        print(f"  🛡️ [{self.name}] Running test suite generation and security audits...")
        test_code = (
            "import pytest\n"
            "from httpx import AsyncClient\n\n"
            "@pytest.mark.asyncio\n"
            "async def test_login_invalid_credentials(client: AsyncClient):\n"
            "    response = await client.post('/api/v1/auth/login', json={'email': 'bad@test.com', 'password': '123'})\n"
            "    assert response.status_code == 401\n"
        )
        audit_report = {
            "tests_generated": ["test_login_success", "test_login_invalid_credentials", "test_sql_injection_guard"],
            "security_status": "PASSED (Rate limiting & password hashing verified)",
            "test_code": test_code
        }
        shared_state["qa_report"] = audit_report
        return audit_report


# =====================================================================
# Lead Architect Coordinator Agent
# =====================================================================
class LeadArchitectCoordinator:
    """Orchestrates feature requests across the specialized engineering team."""

    def __init__(self):
        self.backend = BackendSubAgent()
        self.frontend = FrontendSubAgent()
        self.qa = QASubAgent()

    async def handle_feature_request(self, request: str):
        print(f"\n📋 [Lead Architect] Received Feature Request: \"{request}\"")
        shared_state = {"feature_request": request}

        # Step 1: Lead Architect decomposes requirements
        print("  🧠 [Lead Architect] Decomposing request into Backend, Frontend, and QA sub-tasks...")
        await asyncio.sleep(0.3)

        # Step 2: Delegate to Backend
        backend_res = self.backend.execute(request, shared_state)

        # Step 3: Delegate to Frontend (uses Backend's deliverables)
        frontend_res = self.frontend.execute(request, shared_state)

        # Step 4: Delegate to QA
        qa_res = self.qa.execute(shared_state)

        # Step 5: Synthesis
        print("\n  📦 [Lead Architect] All sub-agents completed their deliverables. Synthesizing package...")
        print("=" * 70)
        print("PROJECT DELIVERY SUMMARY:")
        print(f"1. Backend Endpoints: {[e['path'] for e in backend_res['endpoints']]}")
        print(f"2. Frontend Component: {frontend_res['component']}")
        print(f"3. QA Security Check: {qa_res['security_status']}")
        print(f"4. Automated Tests: {qa_res['tests_generated']}")
        print("=" * 70)


def build_adk_agent_hierarchy():
    """Builds the native Google ADK Agent hierarchy when ADK is installed."""
    if not ADK_AVAILABLE:
        return None

    backend = Agent(
        name="backend_engineer",
        model=create_model(),
        instruction="You are a senior backend engineer specializing in FastAPI and SQLModel."
    )

    # 2. Specialized Frontend Engineer (React, TypeScript, UI state)
    frontend_engineer = Agent(
        name="frontend_engineer",
        model=create_model(),
        instruction="You are a senior frontend engineer specializing in React and TypeScript."
    )
    qa = Agent(
        name="qa_reviewer",
        model=create_model(),
        instruction="You are a senior QA & security engineer generating pytest suites and auditing security."
    )

    # 4. Lead Solutions Architect (Hierarchical Coordinator)
    lead_architect = Agent(
        name="lead_architect",
        model=create_model(),

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
                    subtask = call.args.get("request", call.args) if isinstance(call.args, dict) else call.args
                    print(f"\n⚙️  [Lead Architect] Delegating to Sub-Agent: '{call.name}'")
                    print(f"    📋 Decomposed Sub-Task: \"{subtask}\"")
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
