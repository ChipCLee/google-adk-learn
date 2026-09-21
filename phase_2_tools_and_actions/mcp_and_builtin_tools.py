"""
Phase 2: Built-in Tools & Model Context Protocol (MCP) Integration
Demonstrates:
  - Using Google ADK built-in tools (e.g., load_memory)
  - Integrating external Model Context Protocol (MCP) servers as agent tools
  - Architectural pattern for MCP tool registration
"""

from typing import Dict, Any, List


# Architectural guide & demonstration of Model Context Protocol (MCP) in ADK:
#
# MCP allows agents to connect securely to external systems (databases, GitHub,
# Google Drive, Slack) using standardized JSON-RPC 2.0 messages.
#
# In Google ADK, MCP tools are integrated either via:
# 1. google.adk.tools.mcp (ADK native MCP client)
# 2. Community MCP wrappers (adk-python-community)

class McpToolAdapter:
    """Demonstrates how an MCP Server tool is adapted into an ADK Tool."""

    def __init__(self, server_name: str, tool_name: str, schema: dict):
        self.server_name = server_name
        self.tool_name = tool_name
        self.schema = schema

    def __call__(self, **kwargs) -> Dict[str, Any]:
        """Executes the tool via MCP JSON-RPC protocol."""
        print(f"  [MCP Client] Forwarding call to server '{self.server_name}' -> tool '{self.tool_name}' with args: {kwargs}")
        # In a real MCP setup, this sends:
        # {"jsonrpc": "2.0", "method": "tools/call", "params": {"name": self.tool_name, "arguments": kwargs}}
        if self.tool_name == "query_sqlite_database":
            return {
                "status": "success",
                "rows": [
                    {"ticker": "GOOGL", "shares": 150, "avg_cost": 142.10},
                    {"ticker": "AAPL", "shares": 200, "avg_cost": 180.50},
                ]
            }
        return {"status": "success", "result": f"Executed {self.tool_name} successfully."}


def demonstrate_builtin_tools():
    print("--- 1. Google ADK Built-In Tools ---")
    print("In ADK, built-in tools are imported directly from `google.adk.tools`:\n")
    code_sample = '''
from google.adk.agents import Agent
from google.adk.tools import load_memory
from llm_config import create_model

# Attach a MemoryService to the runner to use this memory tool.
research_agent = Agent(
    name="memory_assistant",
    model=create_model(),
    instruction="Use recalled memories to answer questions about previous sessions.",
    tools=[load_memory]
)

    '''
    print(code_sample.strip())


def demonstrate_mcp_integration():
    print("\n--- 2. Model Context Protocol (MCP) Integration ---")
    print("MCP standardizes how LLM agents interact with tools, filesystems, and databases:\n")

    # Simulate an MCP SQLite tool adapter
    sqlite_mcp_tool = McpToolAdapter(
        server_name="sqlite_portfolio_server",
        tool_name="query_sqlite_database",
        schema={
            "type": "function",
            "name": "query_sqlite_database",
            "description": "Executes a read-only SQL query on the portfolio database.",
            "parameters": {"sql": {"type": "string", "description": "SQL query"}}
        }
    )

    print("Created MCP Tool Adapter: 'query_sqlite_database'")
    print("Simulating agent invocation of MCP tool...")
    result = sqlite_mcp_tool(sql="SELECT ticker, shares, avg_cost FROM portfolio WHERE shares > 0;")
    print(f"Tool Output received by Agent:\n  {result}")


def main():
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
