"""
Phase 2: Financial Market Intelligence & Portfolio Agent
Demonstrates:
  - Defining custom Python functions as tools with docstrings and type hints
  - Using ToolContext to read and modify session state from inside a tool
  - Multi-step tool execution loop
  - Dynamic calculations and state persistence
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
    from google.adk.tools import ToolContext
    ADK_AVAILABLE = bool(os.getenv("GEMINI_API_KEY"))
except ImportError:
    ADK_AVAILABLE = False




# =====================================================================
# Tool Definitions (Standard Python functions with Google-style docstrings)
# =====================================================================

# Mock financial database
MOCK_MARKET_DATA = {
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
    data = MOCK_MARKET_DATA.get(ticker_upper)
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
        ticker: The stock ticker symbol (e.g., GOOGL, MSFT).

    Returns:
        A dictionary containing the calculated P/E ratio and valuation category.
    """
    ticker_upper = ticker.strip().upper()
    data = MOCK_MARKET_DATA.get(ticker_upper)
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


def manage_watchlist(action: str, ticker: str, tool_context: Any = None) -> Dict[str, Any]:
    """Manages the user's active stock watchlist stored in session state.

    Args:
        action: Either 'add', 'remove', or 'view'.
        ticker: The stock ticker to add or remove (optional if action is 'view').
        tool_context: The injected ToolContext providing access to session.state.

    Returns:
        The updated watchlist and status message.
    """
    ticker_upper = ticker.strip().upper() if ticker else ""
    
    # State handling via ToolContext (or mock state object)
    state = getattr(tool_context, "state", {}) if tool_context else {}
    watchlist = state.setdefault("watchlist", ["GOOGL"])  # default starter

    if action.lower() == "add":
        if ticker_upper and ticker_upper not in watchlist:
            watchlist.append(ticker_upper)
            return {"status": "success", "message": f"Added {ticker_upper} to watchlist.", "watchlist": watchlist}
        return {"status": "noop", "message": f"{ticker_upper} is already in watchlist.", "watchlist": watchlist}

    elif action.lower() == "remove":
        if ticker_upper in watchlist:
            watchlist.remove(ticker_upper)
            return {"status": "success", "message": f"Removed {ticker_upper} from watchlist.", "watchlist": watchlist}
        return {"status": "error", "message": f"{ticker_upper} not in watchlist.", "watchlist": watchlist}

    elif action.lower() == "view":
        return {"status": "success", "watchlist": watchlist}

    return {"status": "error", "message": f"Unknown action '{action}'."}


# =====================================================================
# Simulation Runner for Offline Demonstration
# =====================================================================
class MockToolContext:
    def __init__(self, state: dict):
        self.state = state


class SimulatedToolRunner:
    def __init__(self):
        self.state = {"watchlist": ["GOOGL"]}
        self.tools = {
            "get_stock_quote": get_stock_quote,
            "calculate_pe_ratio": calculate_pe_ratio,
            "manage_watchlist": manage_watchlist,
        }

    async def run_turn(self, query: str):
        print(f"\n👤 User Query: \"{query}\"")
        ctx = MockToolContext(self.state)

        # Simulate agent reasoning and tool invocation
        q = query.lower()
        if "pe ratio" in q or "p/e" in q or "valuation" in q:
            ticker = "MSFT" if "msft" in q else "GOOGL"
            print(f"  🤖 Agent calls tool: calculate_pe_ratio(ticker='{ticker}')")
            res = calculate_pe_ratio(ticker)
            print(f"  ⚙️  Tool Result: {res}")
            print(f"  🤖 Agent Response: {ticker} has a P/E ratio of {res['pe_ratio']} ({res['category']} valuation based on {res['formula']}).")

        elif "add" in q and "watchlist" in q:
            ticker = "AAPL" if "aapl" in q else "MSFT"
            print(f"  🤖 Agent calls tool: manage_watchlist(action='add', ticker='{ticker}')")
            res = manage_watchlist(action="add", ticker=ticker, tool_context=ctx)
            print(f"  ⚙️  Tool Result: {res}")
            print(f"  🤖 Agent Response: Successfully added {ticker} to your watchlist. Your current watchlist is now: {res['watchlist']}")

        elif "quote" in q or "price" in q:
            ticker = "GOOGL" if "googl" in q else "AAPL"
            print(f"  🤖 Agent calls tool: get_stock_quote(ticker='{ticker}')")
            res = get_stock_quote(ticker)
            print(f"  ⚙️  Tool Result: {res}")
            print(f"  🤖 Agent Response: {ticker} is trading at ${res['price']} {res['currency']} with a market cap of ${res['market_cap_billions']}B (52w range: ${res['52w_low']} - ${res['52w_high']}).")

        elif "watchlist" in q:
            res = manage_watchlist(action="view", ticker="", tool_context=ctx)
            print(f"  ⚙️  Tool Result: {res}")
            print(f"  🤖 Agent Response: Here is your current watchlist: {res['watchlist']}.")


# =====================================================================
# Main Execution
# =====================================================================
async def main():
    print("=" * 70)
    print("Phase 2: Financial Market Intelligence Agent with Tools & ToolContext")
    print("=" * 70)

    if ADK_AVAILABLE:
        from google.genai import types
        print("[Mode] Live Google ADK")
        agent = Agent(
            name="financial_intelligence_agent",
            model="gemini-2.5-flash",
            instruction="""
            You are an elite equity research assistant.
            Use your available tools to retrieve stock quotes, compute P/E ratios, and manage the user's watchlist.
            Always synthesize tool results into clear, analytical commentary.
            """,
            tools=[get_stock_quote, calculate_pe_ratio, manage_watchlist]
        )
        runner = InMemoryRunner(agent=agent, app_name="financial_app")
        user_id, session_id = "user_corp_892", "session_financial_001"
        try:
            await runner.session_service.create_session(user_id=user_id, session_id=session_id, app_name="financial_app")
        except Exception:
            pass


        queries = [
            "What is the current stock quote for GOOGL?",
            "What is the P/E ratio and valuation of MSFT?",
            "Can you add AAPL to my watchlist?",
            "Show me what's on my watchlist right now."
        ]
        try:
            for q in queries:


                print(f"\n👤 User Query: \"{q}\"")
                msg = types.Content(role="user", parts=[types.Part.from_text(text=q)])
                async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=msg):
                    if hasattr(event, "content") and event.content:
                        if hasattr(event.content, "parts") and event.content.parts:
                            for part in event.content.parts:
                                if hasattr(part, "text") and part.text:
                                    print(f"  🤖 Agent Response: {part.text}")
                        elif isinstance(event.content, str):
                            print(f"  🤖 Agent Response: {event.content}")
                await asyncio.sleep(1)
        except Exception as e:
            if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
                print(f"\n⚠️ [Notice] Gemini Free Tier rate limit reached (5 requests/min). Switching to Simulation Mode.")
                sim = SimulatedToolRunner()
                await sim.run_turn("What is the current stock quote for GOOGL?")
                await sim.run_turn("What is the P/E ratio and valuation of MSFT?")
                await sim.run_turn("Can you add AAPL to my watchlist?")
                await sim.run_turn("Show me what's on my watchlist right now.")
            else:
                raise e

    else:
        print("[Mode] Simulation Mode (google-adk not installed or GEMINI_API_KEY missing)")
        sim = SimulatedToolRunner()
        await sim.run_turn("What is the current stock quote for GOOGL?")
        await sim.run_turn("What is the P/E ratio and valuation of MSFT?")
        await sim.run_turn("Can you add AAPL to my watchlist?")
        await sim.run_turn("Show me what's on my watchlist right now.")


    print("\n" + "=" * 70)
    print("Phase 2 Demo Complete.")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
