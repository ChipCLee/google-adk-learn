"""
Phase 2: Financial Market Intelligence & Portfolio Agent
Demonstrates:
  - Real Google ADK Agent with custom Python tools
  - ToolContext for state-aware tools (reading & modifying session state)
  - Multi-step tool execution loop with live LLM (Gemma 4 on Mac Mini / Gemini)
  - Persistence across turns within a session
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, Any, List

# Keep direct execution (python phase_N/script.py) working from any directory.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from llm_config import ADK_AVAILABLE, create_model, model_description

try:
    from google.adk.agents import Agent
    from google.adk.runners import InMemoryRunner
    from google.adk.tools import ToolContext
except ImportError:
    ADK_AVAILABLE = False
    ToolContext = Any




# =====================================================================
# Financial Registry & Tools
# =====================================================================

MARKET_DATA = {
    "GOOGL": {"price": 182.50, "currency": "USD", "market_cap_b": 2250, "net_income_b": 88.0, "52w_high": 191.0, "52w_low": 130.0},
    "MSFT": {"price": 448.20, "currency": "USD", "market_cap_b": 3330, "net_income_b": 88.1, "52w_high": 468.0, "52w_low": 309.0},
    "AAPL": {"price": 225.00, "currency": "USD", "market_cap_b": 3450, "net_income_b": 100.5, "52w_high": 237.0, "52w_low": 164.0},
}


def get_stock_quote(ticker: str) -> Dict[str, Any]:
    """Retrieves fixed demo market data and statistics for a given stock ticker.

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


def manage_watchlist(action: str, ticker: str, tool_context: ToolContext = None) -> Dict[str, Any]:
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
    watchlist = list(state.get("watchlist", ["GOOGL"]))  # default starter

    if action.lower() == "add":
        if ticker_upper and ticker_upper not in watchlist:
            watchlist.append(ticker_upper)
            state["watchlist"] = watchlist
            state["watchlist"] = watchlist
            return {"status": "success", "message": f"Added {ticker_upper} to watchlist.", "watchlist": watchlist}
        return {"status": "noop", "message": f"{ticker_upper} is already in watchlist.", "watchlist": watchlist}

    elif action.lower() == "remove":
        if ticker_upper in watchlist:
            watchlist.remove(ticker_upper)
            state["watchlist"] = watchlist
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

    if ADK_AVAILABLE:
        from google.genai import types
        print(f"[Mode] Live Google ADK with Ollama ({model_description()})")
        agent = Agent(
            name="financial_intelligence_agent",
            model=create_model(),
            instruction="""
            You are an elite equity research assistant.
            Use your available tools to retrieve stock quotes, compute P/E ratios, and manage the user's watchlist.
            These tools return fixed sample data; label quotes as demo data, not live market prices.
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


                print(f"\n👤 User Query: \"{q}\"")
                msg = types.Content(role="user", parts=[types.Part.from_text(text=q)])
                async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=msg):
                    if hasattr(event, "content") and event.content:
                        if hasattr(event.content, "parts") and event.content.parts:
                            for part in event.content.parts:
                                if hasattr(part, "text") and part.text and not part.thought:
                                    print(f"  🤖 Agent Response: {part.text}")
                        elif isinstance(event.content, str):
                            print(f"  🤖 Agent Response: {event.content}")
                await asyncio.sleep(1)
        except Exception as e:
            if getattr(e, "status_code", None) == 429:
                print(f"\n⚠️ [Notice] Model provider rate limit reached. Switching to Simulation Mode.")
                sim = SimulatedToolRunner()
                await sim.run_turn("What is the current stock quote for GOOGL?")
                await sim.run_turn("What is the P/E ratio and valuation of MSFT?")
                await sim.run_turn("Can you add AAPL to my watchlist?")
                await sim.run_turn("Show me what's on my watchlist right now.")
            else:
                raise e

    else:
        print("[Mode] Simulation Mode (google-adk or litellm not installed)")
        sim = SimulatedToolRunner()
        await sim.run_turn("What is the current stock quote for GOOGL?")
        await sim.run_turn("What is the P/E ratio and valuation of MSFT?")
        await sim.run_turn("Can you add AAPL to my watchlist?")
        await sim.run_turn("Show me what's on my watchlist right now.")


    print("\n" + "=" * 70)
    print("Phase 2 Live Tools Demo Complete.")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
