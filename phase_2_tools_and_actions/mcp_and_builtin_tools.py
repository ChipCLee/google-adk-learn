"""
Phase 2: Built-in Tools & Model Context Protocol (MCP) Integration
Demonstrates:
  - Using Google ADK built-in tools (e.g., google_search)
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
from google.adk.tools import google_search

# The agent now has real-time Google Search grounding
research_agent = Agent(
    name="web_researcher",
    model="gemini-2.5-flash",
    instruction="Use Google Search to answer queries with up-to-date facts.",
    tools=[google_search]
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
    print("Phase 2: Built-in Tools & MCP Protocol Demonstration")
    print("=" * 70)
    demonstrate_builtin_tools()
    demonstrate_mcp_integration()
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
