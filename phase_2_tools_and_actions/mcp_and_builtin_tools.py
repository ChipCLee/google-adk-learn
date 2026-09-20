"""
Phase 2: Built-in Tools & Model Context Protocol (MCP) Integration
Demonstrates:
  - Connecting an ADK Agent to a real external MCP Server via McpToolset
  - Running JSON-RPC 2.0 communication over stdio transport
  - Combining native ADK Python tools with external MCP tools
  - Executing live agent queries with Ollama (Gemma 4 on Mac Mini) or Gemini
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, Any

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.adk.tools import McpToolset
from google.adk.tools.mcp_tool import StdioConnectionParams
from google.adk.models.lite_llm import LiteLlm
from google.genai import types
from mcp import StdioServerParameters


# =====================================================================
# Native ADK Tool (Combined with MCP Tools)
# =====================================================================

def calculate_holding_value(shares: int, current_price: float) -> Dict[str, Any]:
    """Calculates total position value and profit/loss given share count and price.

    Args:
        shares: The number of shares owned.
        current_price: The current market price per share.

    Returns:
        Dictionary with total market value formatted in USD.
    """
    total_val = round(shares * current_price, 2)
    return {
        "shares": shares,
        "current_price": current_price,
        "total_market_value_usd": total_val
    }


# =====================================================================
# Agent Definition & Factory
# =====================================================================

def create_mcp_portfolio_agent(mcp_toolset: McpToolset) -> InMemoryRunner:
    """Creates a real Google ADK Agent equipped with MCP tools and native tools."""
    instructions = """
    You are an intelligent financial portfolio assistant.
    You have access to:
    1. An external MCP SQLite database tool (`query_portfolio_database`) for retrieving user holdings.
    2. A native valuation calculator tool (`calculate_holding_value`) for position pricing.

    Guidelines:
    - When asked about user holdings or stocks owned, ALWAYS call `query_portfolio_database`.
    - When computing total position values, use `calculate_holding_value`.
    - Provide concise, professional, and clear answers (2-3 sentences max).
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
        name="mcp_portfolio_agent",
        model=model,
        instruction=instructions,
        tools=[mcp_toolset, calculate_holding_value]
    )

    return InMemoryRunner(agent=agent, app_name="mcp_portfolio_app")


# =====================================================================
# Main Execution
# =====================================================================

async def main():
    print("=" * 70)
    print("Phase 2: Live Model Context Protocol (MCP) Agent Demonstration")
    print("=" * 70)

    # Resolve path to the real MCP Server script
    server_script = Path(__file__).parent / "portfolio_mcp_server.py"
    print(f"\n[MCP] Connecting to external MCP Server: {server_script.name}")

    # Configure real ADK McpToolset connecting over stdio
    connection_params = StdioConnectionParams(
        server_params=StdioServerParameters(
            command=sys.executable,
            args=[str(server_script)]
        )
    )
    mcp_toolset = McpToolset(connection_params=connection_params)

    # Discover and inspect registered tools from the MCP Server
    tools = await mcp_toolset.get_tools()
    print(f"[MCP] Successfully connected via JSON-RPC 2.0. Discovered MCP Tools:")
    for t in tools:
        print(f"  • {t.name}: {t.description}")

    runner = create_mcp_portfolio_agent(mcp_toolset)
    user_id = "user_investor_501"
    session_id = "session_mcp_001"

    await runner.session_service.create_session(
        user_id=user_id,
        session_id=session_id,
        app_name="mcp_portfolio_app"
    )

    queries = [
        "What stock holdings do I currently own in my portfolio database?",
        "I have 150 shares of GOOGL and current market price is $182.50. What is my total position value?"
    ]

    try:
        for turn_idx, query in enumerate(queries, start=1):
            print(f"\n--- Turn {turn_idx} ---")
            print(f"👤 User: \"{query}\"")
            msg = types.Content(role="user", parts=[types.Part.from_text(text=query)])

            async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=msg):
                if hasattr(event, "content") and event.content:
                    for part in getattr(event.content, "parts", []):
                        if getattr(part, "function_call", None):
                            call = part.function_call
                            print(f"  ⚙️  Tool Executed: {call.name}({call.args})")
                        elif getattr(part, "function_response", None):
                            res = part.function_response
                            print(f"  📥 Tool Result: {res.name} -> {res.response.get('result', res.response)}")
                        elif getattr(part, "text", None) and not getattr(part, "thought", False):
                            print(f"  🤖 Agent: {part.text.strip()}")

    finally:
        # Clean up MCP connection resources
        print("\n[MCP] Closing MCP Server connection...")
        await mcp_toolset.close()

    print("\n" + "=" * 70)
    print("Phase 2 MCP Live Agent Demo Complete.")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
