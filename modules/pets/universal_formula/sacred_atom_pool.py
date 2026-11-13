"""Adapter connecting the Sacred Atom specialists to the bounded task engine.

The 25 slots are execution concurrency, not 25 independent LLM identities.
The existing deterministic local specialists remain the only registered agents.
"""
from modules.pets.sacred_atom_agents import SacredAtomOrchestrator
from .engine import ExecutionEngine
from .policy import PolicyGate


def build_sacred_atom_engine(max_workers=25, checkpoint_path=None):
    """Create a task engine backed by the existing read/analyze/report specialists."""
    orchestrator = SacredAtomOrchestrator()
    handlers = {}

    for agent_id in orchestrator.agents:
        def run(payload, selected_agent=agent_id):
            result = orchestrator.run_agent(selected_agent, payload)
            return {
                "agent_id": result.agent_id,
                "status": result.status,
                "output": result.output,
            }
        handlers[agent_id] = run

    engine = ExecutionEngine(
        handlers=handlers,
        policy=PolicyGate(),
        max_workers=max_workers,
        checkpoint_path=checkpoint_path,
    )
    return engine
