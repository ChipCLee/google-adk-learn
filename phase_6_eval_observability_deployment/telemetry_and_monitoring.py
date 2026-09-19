"""
Phase 6: Telemetry, Observability & Tracing for Google ADK
Demonstrates:
  - Capturing and parsing structured agent events
  - Measuring latency per node/tool
  - Generating OpenTelemetry / Cloud Logging compatible telemetry payloads
"""

import time
import json
from datetime import datetime, timezone
from typing import List, Dict, Any


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


def main():
    print("=" * 75)
    print("Phase 6: Agent Telemetry & OpenTelemetry Tracing Demonstration")
    print("=" * 75)

    collector = TelemetryCollector("adk-contract-compliance-service")

    # Trace 1: Root Agent Invocation
    root_span = collector.start_span("Runner.run_async")

    # Trace 2: LLM Model Generation
    llm_span = collector.start_span("Gemini.generate_content", parent_span_id=root_span)
    time.sleep(0.15)  # simulate LLM latency
    collector.end_span(llm_span, attributes={
        "model": "gemini-2.5-flash",
        "prompt_tokens": 412,
        "completion_tokens": 68,
        "total_tokens": 480
    })


    # Trace 3: Tool Call Execution
    tool_span = collector.start_span("Tool.verify_governing_law", parent_span_id=root_span)
    time.sleep(0.05)  # simulate tool execution
    collector.end_span(tool_span, attributes={
        "tool.name": "verify_governing_law",
        "tool.arguments": {"jurisdiction": "Delaware"},
        "tool.status": "success"
    })

    # End Root Span
    collector.end_span(root_span, attributes={"user_id": "corp_user_771", "session_id": "sess_8911"})

    print("\nGenerated Structured Telemetry Trace (Google Cloud Logging / OTel Format):")
    print(collector.export_cloud_logging_json())

    print("\n" + "=" * 75)
    print("Phase 6 Telemetry Demonstration Complete.")
    print("=" * 75)


if __name__ == "__main__":
    main()
