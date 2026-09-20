"""
Phase 3: Health & Wellness Coach Agent (FitPulse)
Demonstrates:
  - Live Google ADK Agent with state-aware tools (ToolContext)
  - Modifying and reading structured session state across multi-turn conversations
  - Caloric budget tracking, workout logging, and energy balance calculation
  - Running via InMemoryRunner and InMemorySessionService
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
# State-Aware Tools for Wellness Coach
# =====================================================================

def log_meal(meal_name: str, estimated_calories: int, tool_context: ToolContext = None) -> Dict[str, Any]:
    """Logs a meal and updates the user's daily calorie intake in session state.

    Args:
        meal_name: Description of the food or meal (e.g. Oatmeal with berries, Grilled Salmon).
        estimated_calories: Estimated calorie count.
        tool_context: Runtime context providing access to session.state.

    Returns:
        Summary of the meal logged, total consumed today, and remaining calorie budget.
    """
    state = getattr(tool_context, "state", {}) if tool_context else {}
    daily_budget = state.get("daily_calorie_budget", 2000)
    consumed = state.get("calories_consumed", 0) + estimated_calories
    state["calories_consumed"] = consumed

    meals = list(state.get("logged_meals", []))
    meals.append({"meal": meal_name, "calories": estimated_calories})
    state["logged_meals"] = meals

    remaining = daily_budget - consumed
    return {
        "status": "success",
        "meal_logged": meal_name,
        "calories_added": estimated_calories,
        "total_consumed_today": consumed,
        "remaining_budget": remaining,
        "is_over_budget": remaining < 0
    }


def log_workout(workout_type: str, duration_minutes: int, tool_context: ToolContext = None) -> Dict[str, Any]:
    """Logs an exercise activity and calculates calories burned.

    Args:
        workout_type: Type of exercise (e.g. Running, Weightlifting, Swimming, Yoga).
        duration_minutes: Duration of the workout in minutes.
        tool_context: Runtime context providing access to session.state.

    Returns:
        Summary of the workout and estimated calories burned.
    """
    burn_rates = {
        "running": 11,
        "weightlifting": 6,
        "swimming": 9,
        "cycling": 8,
        "yoga": 4
    }
    rate = burn_rates.get(workout_type.lower(), 7)
    calories_burned = rate * duration_minutes

    state = getattr(tool_context, "state", {}) if tool_context else {}
    burned_today = state.get("calories_burned", 0) + calories_burned
    state["calories_burned"] = burned_today

    workouts = list(state.get("logged_workouts", []))
    workouts.append({"type": workout_type, "duration": duration_minutes, "calories_burned": calories_burned})
    state["logged_workouts"] = workouts

    return {
        "status": "success",
        "workout": workout_type,
        "duration_minutes": duration_minutes,
        "calories_burned": calories_burned,
        "total_burned_today": burned_today
    }


def get_daily_health_summary(tool_context: ToolContext = None) -> Dict[str, Any]:
    """Retrieves the complete daily nutrition, workout, and energy balance summary.

    Args:
        tool_context: Runtime context providing access to session.state.

    Returns:
        Full daily summary including net calories and logged items.
    """
    state = getattr(tool_context, "state", {}) if tool_context else {}
    budget = state.get("daily_calorie_budget", 2000)
    consumed = state.get("calories_consumed", 0)
    burned = state.get("calories_burned", 0)
    net = consumed - burned

    return {
        "target_budget": budget,
        "consumed": consumed,
        "burned": burned,
        "net_calories": net,
        "balance_status": "Deficit" if net < budget else "Surplus",
        "meal_count": len(state.get("logged_meals", [])),
        "workout_count": len(state.get("logged_workouts", []))
    }


# =====================================================================
# Agent Definition & Factory
# =====================================================================
def create_wellness_coach_agent() -> InMemoryRunner:
    """Defines and instantiates the FitPulse Wellness Coach Agent with state-aware tools."""
    instructions = """
    You are FitPulse, an energetic, encouraging, and knowledgeable health and wellness coach.
    You help users track their daily nutrition, workouts, and energy balance toward their fitness goals.

    Guidelines:
    1. When a user reports eating food or having a meal, ALWAYS call the `log_meal` tool.
       If estimated calories are not specified by the user, provide a reasonable estimate.
    2. When a user reports exercising or working out, ALWAYS call the `log_workout` tool.
    3. When a user asks for their daily summary, status, scorecard, or progress, ALWAYS call the `get_daily_health_summary` tool.
    4. After executing a tool, ALWAYS reply with a concise, motivating 1-2 sentence response confirming the action and encouraging the user.
    5. Keep your responses focused, concise, and upbeat.
    """

    # Model resolution: local Ollama on Mac Mini by default, or Cloud Gemini if USE_GEMINI=1
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
        name="fitpulse_coach",
        model=model,
        instruction=instructions,
        tools=[log_meal, log_workout, get_daily_health_summary]
    )

    return InMemoryRunner(agent=agent, app_name="fitpulse_app")


# =====================================================================
# Main Execution
# =====================================================================
async def main():
    print("=" * 70)
    print("Phase 3: Health & Wellness Coach Agent (Stateful Session Management)")
    print("=" * 70)

    initial_state = {
        "user_name": "Alex",
        "daily_calorie_budget": 2100,
        "target_weight_kg": 72.0,
        "current_weight_kg": 76.5,
        "calories_consumed": 0,
        "calories_burned": 0,
        "logged_meals": [],
        "logged_workouts": []
    }

    conversation_turns = [
        "Good morning! I just ate a bowl of oatmeal with almonds and blueberries for breakfast (~380 calories).",
        "I just completed a 30-minute outdoor run.",
        "For lunch, I had grilled salmon with quinoa and broccoli (~620 calories).",
        "Can you show me my daily health summary and where I stand?"
    ]

    runner = create_wellness_coach_agent()
    user_id = "user_alex_101"
    session_id = "session_wellness_day_1"

    print(f"Initial Session State: User={initial_state['user_name']}, Budget={initial_state['daily_calorie_budget']} kcal")
    await runner.session_service.create_session(
        user_id=user_id,
        session_id=session_id,
        app_name="fitpulse_app",
        state=initial_state
    )

    for turn_idx, user_msg in enumerate(conversation_turns, start=1):
        print(f"\n--- Turn {turn_idx} ---")
        print(f"👤 Alex: \"{user_msg}\"")
        msg = types.Content(role="user", parts=[types.Part.from_text(text=user_msg)])

        async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=msg):
            if hasattr(event, "content") and event.content:
                for part in getattr(event.content, "parts", []):
                    # Detect tool invocation
                    if getattr(part, "function_call", None):
                        call = part.function_call
                        print(f"  ⚙️  Tool Executed: {call.name}({call.args})")
                    # Detect tool response
                    elif getattr(part, "function_response", None):
                        res = part.function_response
                        print(f"  📥 Tool Result: {res.name} -> {res.response.get('result', res.response)}")
                    # Detect verbal text (excluding internal thoughts)
                    elif getattr(part, "text", None):
                        if not getattr(part, "thought", False):
                            print(f"  🤖 Coach: {part.text.strip()}")

    # Retrieve and display final mutated session state
    session = await runner.session_service.get_session(
        user_id=user_id,
        session_id=session_id,
        app_name="fitpulse_app"
    )
    print("\nFinal Mutated Session State (persisted in runner.session_service):")
    for k, v in session.state.items():
        print(f"  {k}: {v}")

    print("\n" + "=" * 70)
    print("Phase 3 Session State Demo Complete.")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
