"""
Phase 4: Autonomous Software Engineering Team
Demonstrates:
  - Defining specialized sub-agents (Backend, Frontend, QA)
  - Hierarchical coordination via Lead Architect Agent
  - Passing deliverables through shared session state
  - End-to-end task decomposition and synthesis
"""

import asyncio
import os
from typing import Dict, Any, List

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from google.adk.agents import Agent
    from google.adk.runners import InMemoryRunner
    ADK_AVAILABLE = bool(os.getenv("GEMINI_API_KEY"))
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
        model="gemini-2.5-flash",
        instruction="You are a senior backend engineer specializing in FastAPI and SQLModel."
    )
    frontend = Agent(
        name="frontend_engineer",
        model="gemini-2.5-flash",
        instruction="You are a senior frontend engineer specializing in React and TypeScript."
    )
    qa = Agent(
        name="qa_reviewer",
        model="gemini-2.5-flash",
        instruction="You are a senior QA & security engineer generating pytest suites and auditing security."
    )

    lead_architect = Agent(
        name="lead_architect",
        model="gemini-2.5-flash",

        instruction="""
        You are the Lead Solutions Architect.
        Analyze user feature requests, break them down, and delegate tasks to backend_engineer,
        frontend_engineer, and qa_reviewer.
        Synthesize their outputs into a final cohesive engineering report.
        """,
        sub_agents=[backend, frontend, qa]
    )
    return lead_architect


async def main():
    print("=" * 70)
    print("Phase 4: Autonomous Multi-Agent Software Engineering Team")
    print("=" * 70)

    coordinator = LeadArchitectCoordinator()
    await coordinator.handle_feature_request("Build a secure user authentication system with JWT tokens and a login UI.")

    print("\n" + "=" * 70)
    print("Phase 4 Multi-Agent Demo Complete.")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
