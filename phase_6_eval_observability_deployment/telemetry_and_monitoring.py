"""
Phase 6: Telemetry, Observability & Tracing for Google ADK
Demonstrates:
  - Capturing and parsing structured agent events
  - Measuring latency per node/tool
  - Generating OpenTelemetry / Cloud Logging compatible telemetry payloads
"""

import time
import json
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from llm_config import ADK_AVAILABLE, ask_agent, model_description, model_settings
from phase_6_eval_observability_deployment.eval_suite import verify_governing_law


class TelemetryCollector:
    """Collects spans, tool traces, and execution events from ADK runners."""

    def __init__(self, service_name: str = "adk-contract-auditor"):
        self.service_name = service_name
        self.traces: List[Dict[str, Any]] = []

    def start_span(self, name: str, parent_span_id: str = None) -> str:
        span_id = f"span_{len(self.traces) + 1:04d}"
        span = {
            "span_id": span_id,
            "parent_span_id": parent_span_id,
            "name": name,
            "start_time": time.time(),
            "status": "RUNNING",
            "attributes": {}
        }
        self.traces.append(span)
        return span_id

    def end_span(self, span_id: str, attributes: dict = None, error: Exception = None):
        for s in self.traces:
            if s["span_id"] == span_id:
                s["end_time"] = time.time()
                s["duration_ms"] = round((s["end_time"] - s["start_time"]) * 1000, 2)
                s["status"] = "ERROR" if error else "OK"
                if attributes:
                    s["attributes"].update(attributes)
                if error:
                    s["attributes"]["error.message"] = str(error)
                break

    def export_cloud_logging_json(self) -> str:
        """Exports traces in Google Cloud Logging / OpenTelemetry JSON format."""
        payload = {
            "service": self.service_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "spans": self.traces
        }
        return json.dumps(payload, indent=2)


async def main():
    print("=" * 75)
    print("Phase 6: Agent Telemetry & OpenTelemetry Tracing Demonstration")
    print("=" * 75)

    collector = TelemetryCollector("adk-contract-compliance-service")
    print(f"[Mode] Live Ollama telemetry ({model_description()})"
          if ADK_AVAILABLE else "[Mode] Offline telemetry simulation")

    # Trace 1: Root Agent Invocation
    root_span = collector.start_span("Runner.run_async")

    # Trace 2: LLM Model Generation
    llm_span = collector.start_span("Ollama.chat", parent_span_id=root_span)
    if ADK_AVAILABLE:
        result = await ask_agent(
            name="telemetry_demo",
            instruction="Summarize the supplied fictional contract in one sentence. Do not make a legal recommendation.",
            prompt="Mutual NDA with a two-year term and Delaware governing law.",
        )
        print(result["text"])
    else:
        await asyncio.sleep(0.15)
        result = {"tokens_used": 480}
    collector.end_span(llm_span, attributes={
        "model": model_settings()[0],
        "server.address": model_settings()[1],
        "simulated": not ADK_AVAILABLE,
        "total_tokens": result["tokens_used"],
    })


    # Trace 3: Tool Call Execution
    tool_span = collector.start_span("Tool.verify_governing_law", parent_span_id=root_span)
    tool_result = verify_governing_law("Mutual NDA with Delaware governing law.")
    collector.end_span(tool_span, attributes={
        "tool.name": "verify_governing_law",
        "tool.arguments": {"contract_text": "Mutual NDA with Delaware governing law."},
        "tool.status": tool_result["status"],
    })

    # End Root Span
    collector.end_span(root_span, attributes={"user_id": "corp_user_771", "session_id": "sess_8911"})

    print("\nGenerated Structured Telemetry Trace (Google Cloud Logging / OTel Format):")
    print(collector.export_cloud_logging_json())

    print("\n" + "=" * 75)
    print("Phase 6 Telemetry Demonstration Complete.")
    print("=" * 75)


if __name__ == "__main__":
    asyncio.run(main())
