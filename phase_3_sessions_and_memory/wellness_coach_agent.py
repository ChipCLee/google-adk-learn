"""
Phase 3: Health & Wellness Coach Agent (FitPulse)
Demonstrates:
  - Session state lifecycle (session.state)
  - Modifying and reading structured state across multi-turn conversations
  - Caloric budget tracking, workout logging, and goal adaptation
"""

import asyncio
import os
from typing import Dict, Any

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from google.adk.agents import Agent
    from google.adk.runners import InMemoryRunner
    from google.adk.sessions import InMemorySessionService
    from google.adk.tools import ToolContext
    ADK_AVAILABLE = bool(os.getenv("GEMINI_API_KEY"))
except ImportError:
    ADK_AVAILABLE = False




# =====================================================================
# State-Aware Tools for Wellness Coach
# =====================================================================

def log_meal(meal_name: str, estimated_calories: int, tool_context: Any = None) -> Dict[str, Any]:
    """Logs a meal and updates the user's daily calorie intake in session state.

    Args:
        meal_name: Description of the food or meal (e.g. Oatmeal with berries, Grilled Chicken Salad).
        estimated_calories: Estimated calorie count.
        tool_context: Runtime context providing access to session.state.

    Returns:
        Summary of the meal logged, total consumed today, and remaining calorie budget.
    """
    state = getattr(tool_context, "state", {}) if tool_context else {}
    daily_budget = state.setdefault("daily_calorie_budget", 2000)
    consumed = state.setdefault("calories_consumed", 0) + estimated_calories
    state["calories_consumed"] = consumed

    meals = state.setdefault("logged_meals", [])
    meals.append({"meal": meal_name, "calories": estimated_calories})

    remaining = daily_budget - consumed
    return {
        "status": "success",
        "meal_logged": meal_name,
        "calories_added": estimated_calories,
        "total_consumed_today": consumed,
        "remaining_budget": remaining,
        "is_over_budget": remaining < 0
    }


def log_workout(workout_type: str, duration_minutes: int, tool_context: Any = None) -> Dict[str, Any]:
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
    burned_today = state.setdefault("calories_burned", 0) + calories_burned
    state["calories_burned"] = burned_today

    workouts = state.setdefault("logged_workouts", [])
    workouts.append({"type": workout_type, "duration": duration_minutes, "calories_burned": calories_burned})

    return {
        "status": "success",
        "workout": workout_type,
        "duration_minutes": duration_minutes,
        "calories_burned": calories_burned,
        "total_burned_today": burned_today
    }


def get_daily_health_summary(tool_context: Any = None) -> Dict[str, Any]:
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
# Simulation Runner
# =====================================================================
class MockContext:
    def __init__(self, state: dict):
        self.state = state


class SimulatedWellnessSession:
    def __init__(self):
        # Initial user state profile
        self.state = {
            "user_name": "Alex",
            "daily_calorie_budget": 2100,
            "target_weight_kg": 72.0,
            "current_weight_kg": 76.5,
            "calories_consumed": 0,
            "calories_burned": 0,
            "logged_meals": [],
            "logged_workouts": []
        }

    async def execute_turn(self, user_msg: str):
        print(f"\n👤 Alex: \"{user_msg}\"")
        ctx = MockContext(self.state)
        msg_lower = user_msg.lower()

        if "ate" in msg_lower or "breakfast" in msg_lower or "lunch" in msg_lower or "salad" in msg_lower or "oatmeal" in msg_lower:
            # Simulate meal logging
            if "oatmeal" in msg_lower:
                res = log_meal("Oatmeal with almonds & blueberries", 380, ctx)
            else:
                res = log_meal("Grilled salmon with quinoa and broccoli", 620, ctx)
            print(f"  ⚙️  Tool Executed: log_meal -> {res}")
            print(f"  🤖 Coach: Great choice! Logged '{res['meal_logged']}' ({res['calories_added']} kcal). "
                  f"You have consumed {res['total_consumed_today']} kcal today. Remaining budget: {res['remaining_budget']} kcal.")

        elif "ran" in msg_lower or "run" in msg_lower or "workout" in msg_lower or "gym" in msg_lower or "weight" in msg_lower:
            # Simulate workout logging
            res = log_workout("Running", 30, ctx)
            print(f"  ⚙️  Tool Executed: log_workout -> {res}")
            print(f"  🤖 Coach: Awesome job! Logged 30 minutes of running (~{res['calories_burned']} kcal burned). "
                  f"Total active calories burned today: {res['total_burned_today']} kcal.")

        elif "summary" in msg_lower or "status" in msg_lower or "progress" in msg_lower:
            # Simulate summary
            res = get_daily_health_summary(ctx)
            print(f"  ⚙️  Tool Executed: get_daily_health_summary -> {res}")
            print(f"  🤖 Coach: Here is your daily scorecard, {self.state['user_name']}:\n"
                  f"     • Calorie Budget: {res['target_budget']} kcal\n"
                  f"     • Consumed: {res['consumed']} kcal ({res['meal_count']} meals)\n"
                  f"     • Burned: {res['burned']} kcal ({res['workout_count']} workouts)\n"
                  f"     • Net Energy: {res['net_calories']} kcal ({res['balance_status']})\n"
                  f"     You're on track toward your target of {self.state['target_weight_kg']} kg!")


# =====================================================================
# Main Execution
# =====================================================================
async def main():
    print("=" * 70)
    print("Phase 3: Health & Wellness Coach Agent (Stateful Session Management)")
    print("=" * 70)

    sim = SimulatedWellnessSession()

    print(f"Initial Session State: User={sim.state['user_name']}, Budget={sim.state['daily_calorie_budget']} kcal")

    await sim.execute_turn("Good morning! I just ate a bowl of oatmeal with almonds and blueberries for breakfast.")
    await sim.execute_turn("I just completed a 30-minute outdoor run.")
    await sim.execute_turn("For lunch, I had grilled salmon with quinoa and broccoli.")
    await sim.execute_turn("Can you show me my daily health summary and where I stand?")

    print("\nFinal Mutated Session State:")
    for k, v in sim.state.items():
        print(f"  {k}: {v}")

    print("\n" + "=" * 70)
    print("Phase 3 Session State Demo Complete.")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
