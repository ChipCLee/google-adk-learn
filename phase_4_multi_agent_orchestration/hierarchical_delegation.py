"""
Phase 4: Hierarchical Delegation & Dynamic Routing Patterns
Demonstrates:
  - Router Agent vs Supervisor Agent architectures
  - AgentTool (wrapping sub-agents as explicit callable tools)
  - Dynamic routing based on domain classification
"""

from typing import Dict, Any, Callable


class RouterAgent:
    """Routes incoming queries to specialized agents based on classification."""

    def __init__(self):
        self.routes: Dict[str, Callable[[str], str]] = {}

    def register_route(self, intent: str, handler: Callable[[str], str]):
        self.routes[intent] = handler

    def classify_and_dispatch(self, query: str) -> str:
        q = query.lower()
        if any(w in q for w in ["database", "sql", "migration", "schema"]):
            target = "database_expert"
        elif any(w in q for w in ["css", "style", "button", "animation", "react"]):
            target = "ui_expert"
        elif any(w in q for w in ["vulnerability", "auth", "jwt", "encryption", "hack"]):
            target = "security_expert"
        else:
            target = "general_assistant"

        print(f"  🔀 [RouterAgent] Classified query '{query}' -> Intent: '{target}'")
        handler = self.routes.get(target, lambda q: f"Handled by general assistant: {q}")
        return handler(query)


def handle_database(query: str) -> str:
    return "🗄️ [Database Expert] Generated PostgreSQL migration script with index optimization."


def handle_ui(query: str) -> str:
    return "🎨 [UI Expert] Generated Tailwind CSS layout with dark mode support."


def handle_security(query: str) -> str:
    return "🛡️ [Security Expert] Performed OWASP Top 10 vulnerability scan; sanitization applied."


def main():
    print("=" * 70)
    print("Phase 4: Dynamic Agent Routing & AgentTool Demonstration")
    print("=" * 70)

    router = RouterAgent()
    router.register_route("database_expert", handle_database)
    router.register_route("ui_expert", handle_ui)
    router.register_route("security_expert", handle_security)

    queries = [
        "How do I add a unique index to the user email column in PostgreSQL?",
        "How do I fix the button alignment and padding on mobile screens?",
        "Is storing JWT tokens in localStorage vulnerable to XSS attacks?"
    ]

    for q in queries:
        print(f"\nIncoming Request: \"{q}\"")
        result = router.classify_and_dispatch(q)
        print(f"Result: {result}")

    print("\n" + "=" * 70)
    print("Phase 4 Routing Demonstration Complete.")
    print("=" * 70)


if __name__ == "__main__":
    main()
