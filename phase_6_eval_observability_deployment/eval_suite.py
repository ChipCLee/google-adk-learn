"""
Phase 6: Automated Evaluation Suite for ADK Agents
Demonstrates:
  - Benchmark datasets (Golden Test Cases)
  - Measuring tool call accuracy, trajectory efficiency, and rubric scores
  - Computing quantitative evaluation metrics
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from llm_config import ADK_AVAILABLE, ask_agent, model_description


# Benchmark Golden Dataset
BENCHMARK_CASES = [
    {
        "id": "CASE-01",
        "description": "Standard Mutual NDA Review",
        "input_contract": "Mutual NDA with standard 2-year term, Delaware jurisdiction, mutual confidentiality.",
        "expected_tool": "verify_governing_law",
        "expected_status": "APPROVED",
        "expected_keywords": ["Delaware", "approved", "compliant"]
    },
    {
        "id": "CASE-02",
        "description": "Missing Jurisdiction Clause",
        "input_contract": "Vendor NDA with no governing law or dispute resolution clause specified.",
        "expected_tool": "verify_governing_law",
        "expected_status": "FLAGGED",
        "expected_keywords": ["missing", "jurisdiction", "flagged"]
    },
    {
        "id": "CASE-03",
        "description": "Excessive Indemnification Risk",
        "input_contract": "Services agreement with uncapped indemnification and unilateral liability.",
        "expected_tool": "check_liability_cap",
        "expected_status": "REJECTED",
        "expected_keywords": ["uncapped", "liability", "rejected"]
    }
]


# Simulated Contract Auditor Agent
def run_contract_auditor_agent(contract_text: str) -> Dict[str, Any]:
    """Simulates agent evaluation with tool calls and output generation."""
    start_time = time.time()
    c_lower = contract_text.lower()

    called_tool = ""
    status = ""
    commentary = ""

    if "delaware" in c_lower and "mutual" in c_lower:
        called_tool = "verify_governing_law"
        status = "APPROVED"
        commentary = "The contract specifies Delaware governing law and mutual terms. Fully compliant and approved."
    elif "no governing law" in c_lower:
        called_tool = "verify_governing_law"
        status = "FLAGGED"
        commentary = "The contract is missing a mandatory governing law clause. Flagged for legal revision."
    elif "uncapped" in c_lower:
        called_tool = "check_liability_cap"
        status = "REJECTED"
        commentary = "Uncapped indemnification poses unacceptable financial risk. Rejected per corporate guidelines."
    else:
        called_tool = "general_review"
        status = "INCONCLUSIVE"
        commentary = "Requires manual legal counsel review."

    latency_ms = round((time.time() - start_time) * 1000 + 45, 1)  # simulated latency
    return {
        "status": status,
        "called_tool": called_tool,
        "commentary": commentary,
        "latency_ms": latency_ms,
        "tokens_used": 340
    }


def verify_governing_law(contract_text: str) -> dict:
    """Check whether the sample contract states Delaware governing law.

    Args:
        contract_text: The supplied sample contract text.
    """
    if "delaware" in contract_text.lower():
        return {"status": "APPROVED", "commentary": "Delaware governing law is present; approved and compliant with this demo's policy."}
    return {"status": "FLAGGED", "commentary": "Missing jurisdiction clause; flagged for review."}


def check_liability_cap(contract_text: str) -> dict:
    """Check the sample contract for uncapped liability.

    Args:
        contract_text: The supplied sample contract text.
    """
    if "uncapped" in contract_text.lower():
        return {"status": "REJECTED", "commentary": "Uncapped liability; rejected under this demo's policy."}
    return {"status": "INCONCLUSIVE", "commentary": "Requires further review."}


async def run_live_contract_auditor(contract_text: str) -> dict:
    from pydantic import BaseModel

    class Verdict(BaseModel):
        status: str
        commentary: str

    start = time.perf_counter()
    result = await ask_agent(
        name="contract_auditor",
        instruction=(
            "Evaluate this fictional sample against the demo policy. Use "
            "check_liability_cap for indemnification/liability questions; otherwise "
            "use verify_governing_law. You must call the appropriate tool. "
            "Report its status and explain its findings, retaining relevant terms."
        ),
        prompt=contract_text,
        tools=[verify_governing_law, check_liability_cap], output_schema=Verdict,
    )
    verdict = Verdict.model_validate_json(result["text"]).model_dump()
    return {
        **verdict,
        "called_tool": result["tool_calls"][0] if result["tool_calls"] else "",
        "latency_ms": round((time.perf_counter() - start) * 1000, 1),
        "tokens_used": result["tokens_used"],
    }


async def evaluate_agent():
    print("=" * 75)
    print(f"[Mode] Live Ollama evaluation ({model_description()})"
          if ADK_AVAILABLE else "[Mode] Offline evaluation simulation")
    print("Phase 6: Automated Agent Evaluation Benchmark Runner")
    print("=" * 75)

    results = []
    total_cases = len(BENCHMARK_CASES)
    passed_cases = 0

    for case in BENCHMARK_CASES:
        print(f"\nEvaluating {case['id']}: \"{case['description']}\"")
        output = (
            await run_live_contract_auditor(case["input_contract"])
            if ADK_AVAILABLE else run_contract_auditor_agent(case["input_contract"])
        )

        # Metric 1: Tool Call Accuracy
        tool_match = output["called_tool"] == case["expected_tool"]

        # Metric 2: Status Accuracy
        status_match = output["status"] == case["expected_status"]

        # Metric 3: Keyword Coverage
        keyword_hits = sum(1 for kw in case["expected_keywords"] if kw.lower() in output["commentary"].lower())
        keyword_score = round((keyword_hits / len(case["expected_keywords"])) * 5.0, 1)

        case_passed = tool_match and status_match and (keyword_score >= 3.0)
        if case_passed:
            passed_cases += 1

        print(f"  • Tool Selected:     {output['called_tool']} (Expected: {case['expected_tool']}) -> {'✅' if tool_match else '❌'}")
        print(f"  • Verdict:           {output['status']} (Expected: {case['expected_status']}) -> {'✅' if status_match else '❌'}")
        print(f"  • Rubric Score:      {keyword_score} / 5.0")
        print(f"  • Latency:           {output['latency_ms']} ms | Tokens: {output['tokens_used']}")
        print(f"  • Overall Result:    {'PASS ✅' if case_passed else 'FAIL ❌'}")

        results.append({
            "id": case["id"],
            "tool_match": tool_match,
            "status_match": status_match,
            "score": keyword_score,
            "latency": output["latency_ms"],
            "passed": case_passed
        })

    # Benchmark Summary
    print("\n" + "=" * 75)
    print("BENCHMARK EVALUATION SUMMARY")
    print("=" * 75)
    accuracy_pct = round((passed_cases / total_cases) * 100, 1)
    avg_latency = round(sum(r["latency"] for r in results) / total_cases, 1)
    avg_score = round(sum(r["score"] for r in results) / total_cases, 2)

    print(f"Total Benchmark Cases: {total_cases}")
    print(f"Passed:                {passed_cases}/{total_cases} ({accuracy_pct}%)")
    print(f"Average Rubric Score:  {avg_score} / 5.0")
    print(f"Average Latency:       {avg_latency} ms")
    print(f"Benchmark Status:      {'PASSED (demo cases only)' if accuracy_pct == 100.0 else 'NEEDS IMPROVEMENT'}")
    print("=" * 75)


if __name__ == "__main__":
    asyncio.run(evaluate_agent())
