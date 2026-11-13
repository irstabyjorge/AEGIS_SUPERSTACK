"""Adapter connecting Sacred Atom specialists to the bounded task engine.

The 25 slots are execution concurrency, not 25 independent LLM identities.
The existing deterministic local specialists remain the only registered agents.
"""
from modules.pets.sacred_atom_agents import AgentResult, SacredAtomOrchestrator
from .engine import ExecutionEngine
from .policy import PolicyGate


def build_sacred_atom_engine(max_workers=25, checkpoint_path=None):
    """Create a task engine backed by existing read/analyze/report specialists."""
    orchestrator = SacredAtomOrchestrator()
    handlers = {}

    for agent_id in orchestrator.agents:
        def run(payload, selected_agent=agent_id):
            worker_payload = dict(payload)
            dependency_results = worker_payload.pop("_dependency_results", {})
            if selected_agent == "DODECA_COORDINATOR":
                worker_payload["results"] = [
                    AgentResult(
                        agent_id=value["agent_id"],
                        output=value.get("output", {}),
                        status=value.get("status", "completed"),
                    )
                    for _, value in sorted(dependency_results.items())
                    if isinstance(value, dict) and value.get("agent_id")
                ]
            else:
                worker_payload.pop("_dependency_results", None)
            result = orchestrator.run_agent(selected_agent, worker_payload)
            return {
                "agent_id": result.agent_id,
                "status": result.status,
                "output": result.output,
            }
        handlers[agent_id] = run

    return ExecutionEngine(
        handlers=handlers,
        policy=PolicyGate(),
        max_workers=max_workers,
        checkpoint_path=checkpoint_path,
    )
