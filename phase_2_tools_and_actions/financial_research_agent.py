"""
Phase 2: Financial Market Intelligence & Portfolio Agent
Demonstrates:
  - Real Google ADK Agent with custom Python tools
  - ToolContext for state-aware tools (reading & modifying session state)
  - Multi-step tool execution loop with live LLM (Gemma 4 on Mac Mini / Gemini)
  - Persistence across turns within a session
"""

import asyncio
import os
from typing import Dict, Any

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.adk.tools import ToolContext
from google.adk.models.lite_llm import LiteLlm
from google.genai import types


# =====================================================================
# Financial Registry & Tools
# =====================================================================

MARKET_DATA = {
    "GOOGL": {"price": 182.50, "currency": "USD", "market_cap_b": 2250, "net_income_b": 88.0, "52w_high": 191.0, "52w_low": 130.0},
    "MSFT": {"price": 448.20, "currency": "USD", "market_cap_b": 3330, "net_income_b": 88.1, "52w_high": 468.0, "52w_low": 309.0},
    "AAPL": {"price": 225.00, "currency": "USD", "market_cap_b": 3450, "net_income_b": 100.5, "52w_high": 237.0, "52w_low": 164.0},
}


def get_stock_quote(ticker: str) -> Dict[str, Any]:
    """Retrieves real-time market quote and statistics for a given stock ticker.

    Args:
        ticker: The stock ticker symbol (e.g., GOOGL, MSFT, AAPL).

    Returns:
        A dictionary containing price, currency, market cap, and 52-week range.
    """
    ticker_upper = ticker.strip().upper()
    data = MARKET_DATA.get(ticker_upper)
    if not data:
        return {"error": f"Ticker '{ticker_upper}' not found in market registry."}
    return {
        "ticker": ticker_upper,
        "price": data["price"],
        "currency": data["currency"],
        "market_cap_billions": data["market_cap_b"],
        "52w_high": data["52w_high"],
        "52w_low": data["52w_low"]
    }


def calculate_pe_ratio(ticker: str) -> Dict[str, Any]:
    """Calculates the Price-to-Earnings (P/E) valuation ratio for a given stock.

    Args:
        ticker: The stock ticker symbol (e.g., GOOGL, MSFT, AAPL).

    Returns:
        A dictionary containing the calculated P/E ratio and valuation category.
    """
    ticker_upper = ticker.strip().upper()
    data = MARKET_DATA.get(ticker_upper)
    if not data:
        return {"error": f"Ticker '{ticker_upper}' not found."}

    pe = round(data["market_cap_b"] / data["net_income_b"], 2)
    category = "Growth" if pe > 30 else "Value" if pe < 20 else "Balanced"
    return {
        "ticker": ticker_upper,
        "pe_ratio": pe,
        "category": category,
        "formula": "Market Cap / Net Income"
    }


def manage_watchlist(action: str, ticker: str = "", tool_context: ToolContext = None) -> Dict[str, Any]:
    """Manages the user's active stock watchlist stored in session state.

    Args:
        action: Either 'add', 'remove', or 'view'.
        ticker: The stock ticker to add or remove (optional if action is 'view').
        tool_context: The injected ToolContext providing access to session.state.

    Returns:
        The updated watchlist and status message.
    """
    ticker_upper = ticker.strip().upper() if ticker else ""
    state = getattr(tool_context, "state", {}) if tool_context else {}
    watchlist = list(state.get("watchlist", ["GOOGL"]))

    if action.lower() == "add":
        if ticker_upper and ticker_upper not in watchlist:
            watchlist.append(ticker_upper)
            state["watchlist"] = watchlist
            return {"status": "success", "message": f"Added {ticker_upper} to watchlist.", "watchlist": watchlist}
        return {"status": "noop", "message": f"{ticker_upper} is already in watchlist.", "watchlist": watchlist}

    elif action.lower() == "remove":
        if ticker_upper in watchlist:
            watchlist.remove(ticker_upper)
            state["watchlist"] = watchlist
            return {"status": "success", "message": f"Removed {ticker_upper} from watchlist.", "watchlist": watchlist}
        return {"status": "error", "message": f"{ticker_upper} not in watchlist.", "watchlist": watchlist}

    elif action.lower() == "view":
        return {"status": "success", "watchlist": watchlist}

    return {"status": "error", "message": f"Unknown action '{action}'."}


# =====================================================================
# Agent Definition & Factory
# =====================================================================
def create_financial_research_agent() -> InMemoryRunner:
    """Creates the Financial Intelligence Agent with state-aware market tools."""
    instructions = """
    You are an elite equity research and portfolio assistant.
    Your responsibilities:
    1. Use your available tools to retrieve stock quotes, compute P/E ratios, and manage the user's watchlist.
    2. Always synthesize tool results into clear, concise, and analytical commentary (2 to 3 sentences maximum).
    3. After executing a tool, confirm the action or data directly to the user.
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
        name="financial_intelligence_agent",
        model=model,
        instruction=instructions,
        tools=[get_stock_quote, calculate_pe_ratio, manage_watchlist]
    )

    return InMemoryRunner(agent=agent, app_name="financial_app")


# =====================================================================
# Main Execution
# =====================================================================
async def main():
    print("=" * 70)
    print("Phase 2: Financial Market Intelligence Agent with Live Tools")
    print("=" * 70)

    runner = create_financial_research_agent()
    user_id = "user_corp_892"
    session_id = "session_financial_001"

    # Initialize session state with a starter watchlist
    initial_state = {"watchlist": ["GOOGL"]}
    print(f"Initial Session State: Watchlist={initial_state['watchlist']}")
    await runner.session_service.create_session(
        user_id=user_id,
        session_id=session_id,
        app_name="financial_app",
        state=initial_state
    )

    queries = [
        "What is the current stock quote for GOOGL?",
        "What is the P/E ratio and valuation of MSFT?",
        "Can you add AAPL to my watchlist?",
        "Show me what's on my watchlist right now."
    ]

    for turn_idx, q in enumerate(queries, start=1):
        print(f"\n--- Turn {turn_idx} ---")
        print(f"👤 User: \"{q}\"")
        msg = types.Content(role="user", parts=[types.Part.from_text(text=q)])

        async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=msg):
            if hasattr(event, "content") and event.content:
                for part in getattr(event.content, "parts", []):
                    # Tool call
                    if getattr(part, "function_call", None):
                        call = part.function_call
                        print(f"  ⚙️  Tool Executed: {call.name}({call.args})")
                    # Tool response
                    elif getattr(part, "function_response", None):
                        res = part.function_response
                        print(f"  📥 Tool Result: {res.name} -> {res.response.get('result', res.response)}")
                    # Agent verbal response (excluding internal thought)
                    elif getattr(part, "text", None):
                        if not getattr(part, "thought", False):
                            print(f"  🤖 Agent: {part.text.strip()}")

    # Retrieve and inspect persisted session state
    session = await runner.session_service.get_session(
        user_id=user_id,
        session_id=session_id,
        app_name="financial_app"
    )
    print("\nFinal Mutated Session State (persisted in runner.session_service):")
    for k, v in session.state.items():
        print(f"  {k}: {v}")

    print("\n" + "=" * 70)
    print("Phase 2 Live Tools Demo Complete.")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
