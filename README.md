# Mastering Google ADK (Agent Development Kit) 🚀

Welcome to the comprehensive, hands-on curriculum for mastering the **Google Agent Development Kit (ADK)**. 

The Google ADK is an open-source, code-first framework designed by Google for building, orchestrating, evaluating, and deploying production-grade AI agents and multi-agent systems.

---

## 🗺️ Curriculum Roadmap

The curriculum is structured into 6 progressive phases, each containing:
- In-depth architectural documentation (`README.md`)
- Production-ready, runnable Python code
- Real-world enterprise use cases
- Both live Gemini execution and offline simulation modes

```
google-adk/
├── README.md                               # Master Curriculum Roadmap (this file)
├── requirements.txt                        # Global dependencies
├── .env.example                            # Configuration & API keys
│
├── phase_1_foundations/                    # Phase 1: Core Mechanics & Single-Agent Fundamentals
│   ├── README.md                           # Architecture, Agent/LlmAgent, InMemoryRunner, Event Loop
│   ├── customer_support_agent.py           # Real Use Case: Customer Support Triage & FAQ Agent
│   └── run_interactive.py                  # Interactive CLI session runner
│
├── phase_2_tools_and_actions/              # Phase 2: Custom Tools, Context & External Integrations
│   ├── README.md                           # Function calling, ToolContext, State mutation, MCP
│   ├── financial_research_agent.py         # Real Use Case: Financial Intelligence & Portfolio Agent
│   └── mcp_and_builtin_tools.py            # Built-in tools & Model Context Protocol (MCP) integration
│
├── phase_3_sessions_and_memory/            # Phase 3: Sessions, State Persistence & Long-Term Memory
│   ├── README.md                           # Session lifecycle, SessionService, MemoryService, Isolation
│   ├── wellness_coach_agent.py             # Real Use Case: Health & Wellness Coach with persistent state
│   └── memory_service_demo.py              # Semantic search & long-term memory recall
│
├── phase_4_multi_agent_orchestration/      # Phase 4: Multi-Agent Systems & Task Delegation
│   ├── README.md                           # Sub-agents, AgentTool, Router patterns, Agent hierarchy
│   ├── software_team_agents.py             # Real Use Case: Autonomous Software Dev Team (Arch/Dev/QA)
│   └── hierarchical_delegation.py          # Dynamic delegation & collaborative state sharing
│
├── phase_5_workflows_and_hitl/             # Phase 5: Graph Workflows & Human-in-the-Loop (HITL)
│   ├── README.md                           # Deterministic graph execution, branches, loops, HITL gates
│   ├── incident_remediation_workflow.py    # Real Use Case: Enterprise Incident Triage & Auto-Remediation
│   └── human_in_the_loop_gate.py           # Pausing, state snapshotting, human approval, and resumption
│
└── phase_6_eval_observability_deployment/  # Phase 6: Evaluation, Telemetry & Production Deployment
    ├── README.md                           # Eval metrics, tracing (Monocle/OTel), Cloud Run, adk web
    ├── eval_suite.py                       # Automated benchmark test suite & evaluation rubrics
    ├── telemetry_and_monitoring.py         # Structured event telemetry & observability hooks
    ├── Dockerfile                          # Production container configuration
    └── deploy_cloud_run.sh                 # Cloud Run deployment script
```

---

## ⚡ Quickstart & Setup

### 1. Prerequisites
- Python 3.10+
- A Google AI Studio API Key (or Google Cloud project with Vertex AI enabled)

### 2. Environment Setup

#### Using `uv` (Recommended)
```bash
# Clone or navigate to the repository
cd google-adk

# Install dependencies and sync environment with uv
uv sync

# Run any script with uv
uv run python phase_1_foundations/customer_support_agent.py

# Add or manage dependencies with uv
uv add <package-name>
```

#### Standard `pip` Setup
```bash
# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and paste your GEMINI_API_KEY
```

---

## 📚 Phase Summaries & Learning Path

| Phase | Focus Area | Real-World Use Case | Key ADK Concepts |
|---|---|---|---|
| **Phase 1** | **Foundations & Core Mechanics** | Customer Support Triage | `Agent`, `InMemoryRunner`, `run_async`, Event Streaming |
| **Phase 2** | **Tools & Dynamic Actions** | Financial Market Intelligence | `FunctionTool`, `ToolContext`, State Mutation, MCP |
| **Phase 3** | **Sessions & Memory Persistence** | Health & Wellness Coach | `SessionService`, `session.state`, `MemoryService` |
| **Phase 4** | **Multi-Agent Orchestration** | Software Dev Team (Arch/Dev/QA) | `sub_agents`, `AgentTool`, Coordinator/Router |
| **Phase 5** | **Graph Workflows & HITL** | IT Incident Auto-Remediation | Graph Runtime, Conditional Branches, HITL Approval |
| **Phase 6** | **Evaluation & Production** | Enterprise Compliance Auditor | Eval Metrics, Telemetry/Tracing, Docker, Cloud Run |

---

## 💡 Dual Execution Modes (Live & Offline Simulation)

Every Python example in this repository is built with **dual execution support**:
1. **Live Mode**: If `GEMINI_API_KEY` is set and `google-adk` is installed, it connects to Gemini models (`gemini-2.0-flash`) in real-time.
2. **Simulation / Fallback Mode**: If running in an offline environment or without credentials, each script demonstrates full execution flows, state mutations, and event traces via mock adapters, allowing you to learn the exact lifecycle without API keys.
