"""
Phase 5: Human-in-the-Loop (HITL) Authorization Gate Demo
Demonstrates:
  - Pausing workflow execution before high-risk actions
  - State snapshotting and persistence during pause
  - Resuming execution upon human approval or rejection
  - Safety constraints for autonomous agents
"""

import asyncio
from typing import Dict, Any, Optional


class HitlWorkflowState:
    """Manages serializable state for pause/resume lifecycle."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.status = "INITIALIZED"
        self.pending_action: Optional[Dict[str, Any]] = None
        self.history = []

    def pause_for_approval(self, action_name: str, payload: dict, risk_reason: str):
        self.status = "PAUSED_PENDING_APPROVAL"
        self.pending_action = {
            "action": action_name,
            "payload": payload,
            "risk_reason": risk_reason
        }
        print(f"\n⏸️  [HITL Engine] Execution PAUSED for Session '{self.session_id}'")
        print(f"    Pending Action: {action_name}")
        print(f"    Target:         {payload}")
        print(f"    Risk Reason:    {risk_reason}")
        print(f"    State successfully snapshotted to persistent storage.")

    def resume_with_decision(self, approved: bool, operator_id: str, comments: str = "") -> str:
        if self.status != "PAUSED_PENDING_APPROVAL":
            raise ValueError("Cannot resume a workflow that is not paused.")

        action = self.pending_action
        if approved:
            self.status = "RESUMED_EXECUTING"
            print(f"\n▶️  [HITL Engine] Resuming Session '{self.session_id}' - APPROVED by {operator_id}")
            print(f"    Operator Comments: \"{comments}\"")
            print(f"    Executing: {action['action']}({action['payload']})...")
            self.status = "COMPLETED"
            return f"Action '{action['action']}' executed successfully."
        else:
            self.status = "ABORTED_BY_OPERATOR"
            print(f"\n🚫 [HITL Engine] Session '{self.session_id}' - REJECTED by {operator_id}")
            print(f"    Operator Comments: \"{comments}\"")
            print(f"    Rolling back changes and notifying incident commander.")
            return f"Action '{action['action']}' rejected and aborted."


def main():
    print("=" * 70)
    print("Phase 5: Human-in-the-Loop (HITL) Gate Simulation")
    print("=" * 70)

    # Scenario 1: Operator Approves
    print("\n>>> Scenario A: High-Risk Database Migration (Approved) <<<")
    state_a = HitlWorkflowState("sess_migration_901")
    state_a.pause_for_approval(
        action_name="execute_database_drop_column",
        payload={"table": "customers", "column": "legacy_ssn_hash"},
        risk_reason="Irreversible data drop on production database cluster"
    )

    # Simulated operator review
    result_a = state_a.resume_with_decision(
        approved=True,
        operator_id="DBA-Lead (@marcus_data)",
        comments="Backup verified on S3; column confirmed deprecated in v3.0."
    )
    print(f"Result: {result_a}")

    # Scenario 2: Operator Rejects
    print("\n>>> Scenario B: Automated Traffic Blackhole (Rejected) <<<")
    state_b = HitlWorkflowState("sess_ddos_guard_902")
    state_b.pause_for_approval(
        action_name="null_route_ip_subnet",
        payload={"cidr": "198.51.100.0/24"},
        risk_reason="Subnet includes legitimate enterprise customer traffic"
    )

    result_b = state_b.resume_with_decision(
        approved=False,
        operator_id="Security-Ops (@elena_sec)",
        comments="Do not blackhole subnet; apply rate-limit of 500 req/s instead."
    )
    print(f"Result: {result_b}")

    print("\n" + "=" * 70)
    print("Phase 5 HITL Gate Demonstration Complete.")
    print("=" * 70)


if __name__ == "__main__":
    main()
