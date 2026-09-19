"""
Phase 1: Interactive CLI Session Runner
Allows you to chat live with the Phase 1 Customer Support Agent from your terminal.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from customer_support_agent import create_customer_support_agent, ADK_AVAILABLE

try:
    from google.genai import types
except ImportError:
    types = None


async def interactive_session():
    print("=" * 70)
    print("Phase 1: Interactive Chat with CloudScale Support Agent")
    print("Type 'exit', 'quit', or press Ctrl+C to terminate the session.")
    print("=" * 70)

    runner = create_customer_support_agent()
    user_id = "interactive_user"
    session_id = "interactive_session_001"

    if ADK_AVAILABLE and hasattr(runner, "session_service"):
        try:
            await runner.session_service.create_session(user_id=user_id, session_id=session_id, app_name="cloudscale_support")
        except Exception:
            pass


    while True:
        try:
            user_msg = input("\n👤 You: ").strip()
            if not user_msg:
                continue
            if user_msg.lower() in ("exit", "quit", "q"):
                print("Ending session. Goodbye!")
                break

            print("🤖 Agent: ", end="", flush=True)

            msg = types.Content(role="user", parts=[types.Part.from_text(text=user_msg)]) if (ADK_AVAILABLE and types) else user_msg

            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=msg
            ):
                if hasattr(event, "content") and event.content:
                    if hasattr(event.content, "parts") and event.content.parts:
                        for part in event.content.parts:
                            if hasattr(part, "text") and part.text:
                                print(f"\n{part.text}")
                    elif isinstance(event.content, str):
                        print(f"\n{event.content}")
        except (KeyboardInterrupt, EOFError):
            print("\nSession interrupted. Goodbye!")
            break


if __name__ == "__main__":
    asyncio.run(interactive_session())

