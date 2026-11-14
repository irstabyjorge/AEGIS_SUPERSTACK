"""Safe API adapter for the existing PETS Universal Formula engine.

Only bounded, local read/analyze/report handlers are used. This adapter does
not persist user submissions, access networks, mutate source files, or invoke
external actions.
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from modules.pets.sacred_atom_agents import Evidence
from modules.pets.universal_formula.objective import run_objective
from modules.pets.universal_formula.engine import TaskStatus


def evaluate_objective(*, objective: str, evidence: list[dict],
                       domains: list[str], options: list[str]) -> dict:
    evidence_records = [
        Evidence(
            evidence_id=item["evidence_id"],
            source=item["source"],
            claim=item["claim"],
            status="unverified",
            observed_at=item.get("observed_at"),
        )
        for item in evidence
    ]
    engine, state = run_objective(
        objective=objective,
        evidence=evidence_records,
        domains=domains,
        options=options,
        max_workers=5,
        checkpoint_path=None,
    )
    task_counts: dict[str, int] = {}
    for task in state.values():
        task_counts[task["status"]] = task_counts.get(task["status"], 0) + 1
    all_passed = all(
        task["status"] == TaskStatus.PASSED.value for task in state.values()
    )
    if not all_passed:
        raise RuntimeError("Universal Formula objective did not complete cleanly")

    validator = state["07_validate"]["result"]["output"]
    return {
        "run_id": str(uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "formula": "PETS Universal Formula",
        "cycle": [
            "Observe", "Classify", "Constrain", "Reason", "Validate",
            "Authorize", "Act", "Record", "Learn",
        ],
        "execution_mode": "bounded_local_analysis",
        "objective": objective,
        "task_counts": task_counts,
        "tasks": state,
        "evidence_validation": {
            "submitted_records": len(evidence_records),
            "provenance_fields_present": validator["all_valid"],
            "checks": validator["checks"],
            "epistemic_limit": "Provenance presence does not establish that a claim is true; submitted records remain unverified.",
        },
        "safety": {
            "network_access": False,
            "external_actions": False,
            "source_mutation": False,
            "canonical_memory_write": False,
            "persistent_storage": False,
            "human_review_required_for_changes": True,
        },
    }
