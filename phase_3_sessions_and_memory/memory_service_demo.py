"""
Phase 3: Long-Term Semantic Memory (MemoryService) Demo
Demonstrates:
  - Difference between ephemeral session state and cross-session semantic memory
  - Ingesting episodic facts (user preferences, medical conditions, past events)
  - Semantic retrieval across independent sessions using vector similarity
"""

import math
from typing import List, Dict, Any


class MemoryRecord:
    """Represents an atomic semantic memory entry in ADK MemoryService."""

    def __init__(self, memory_id: str, content: str, tags: List[str], embedding: List[float]):
        self.memory_id = memory_id
        self.content = content
        self.tags = tags
        self.embedding = embedding

    def __repr__(self):
        return f"<Memory [{self.memory_id}] {self.content}>"


class MockMemoryService:
    """Simulates the ADK MemoryService with vector embedding & cosine similarity."""

    def __init__(self):
        self.records: List[MemoryRecord] = []

    def _simple_text_embed(self, text: str) -> List[float]:
        """Simple deterministic mock embedding for demonstration."""
        # Generates a pseudo-vector based on character frequencies
        text_lower = text.lower()
        keywords = ["knee", "injury", "allergy", "gluten", "cardio", "vegan", "running", "squat", "weight"]
        vec = [float(text_lower.count(kw)) for kw in keywords]
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]

    def add_memory(self, memory_id: str, content: str, tags: List[str]):
        """Persists a new fact into long-term memory."""
        embedding = self._simple_text_embed(content)
        record = MemoryRecord(memory_id, content, tags, embedding)
        self.records.append(record)
        print(f"  🧠 [MemoryService] Stored: \"{content}\" (Tags: {tags})")

    def search_memories(self, query: str, top_k: int = 2) -> List[Dict[str, Any]]:
        """Retrieves top-k most relevant memories using cosine similarity."""
        query_vec = self._simple_text_embed(query)
        scored = []

        for r in self.records:
            # Cosine similarity
            dot = sum(a * b for a, b in zip(r.embedding, query_vec))
            scored.append((dot, r))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, rec in scored[:top_k]:
            results.append({
                "memory_id": rec.memory_id,
                "content": rec.content,
                "similarity_score": round(score, 3),
                "tags": rec.tags
            })
        return results


def main():
    print("=" * 70)
    print("Phase 3: Long-Term Semantic Memory (MemoryService) Demonstration")
    print("=" * 70)

    memory_service = MockMemoryService()

    print("\n--- Step 1: Ingesting Facts from Past Sessions (Days/Weeks Ago) ---")
    memory_service.add_memory(
        memory_id="mem_001",
        content="User experienced a right meniscus knee tear in 2024; instructed to avoid high-impact squats.",
        tags=["medical", "injury", "knee"]
    )
    memory_service.add_memory(
        memory_id="mem_002",
        content="User has a diagnosed gluten allergy; requires 100% gluten-free meal recommendations.",
        tags=["nutrition", "allergy", "gluten"]
    )
    memory_service.add_memory(
        memory_id="mem_003",
        content="User prefers morning cardio workouts between 6:30 AM and 7:15 AM.",
        tags=["preference", "routine", "cardio"]
    )

    print("\n--- Step 2: New Conversation Session (Zero Session State) ---")
    print("A new session starts: session_id='session_new_month_turn_01'.")
    print("User asks: 'Can you recommend a leg workout and a post-workout recovery breakfast?'")

    print("\n--- Step 3: Agent Queries MemoryService with Query Context ---")
    print("Agent retrieves memories matching 'leg workout exercise and gluten breakfast'...")

    retrieved = memory_service.search_memories("knee injury workout gluten allergy meal", top_k=2)
    for idx, match in enumerate(retrieved, start=1):
        print(f"  Match #{idx} [Score: {match['similarity_score']}]: {match['content']}")

    print("\n--- Step 4: Agent Synthesizes Response Using Recalled Long-Term Facts ---")
    response = (
        "🤖 Coach: 'Welcome back! Given your previous right meniscus knee injury, we will skip "
        "heavy squats and high-impact jumps today. Instead, let's focus on low-impact knee-friendly "
        "movements: straight-leg raises, hamstring bridges, and seated leg curls.\n\n"
        "For your post-workout breakfast, keeping your gluten-free requirement in mind, I recommend "
        "a certified gluten-free oat bowl with chia seeds and almond butter, paired with a whey/pea protein shake.'"
    )
    print(response)

    print("\n" + "=" * 70)
    print("Phase 3 MemoryService Demo Complete.")
    print("=" * 70)


if __name__ == "__main__":
    main()
