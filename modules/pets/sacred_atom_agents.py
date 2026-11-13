"""PETS/AEGIS Sacred Atom multi-agent engine.
Pure local orchestration primitives: no network, daemon, dynamic imports,
code execution, external actions, or autonomous memory writes.
Geometry names are organizational metaphors, not consciousness claims.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Iterable

SAFE_CAPABILITIES = frozenset({"read", "analyze", "report"})

@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    source: str
    claim: str
    status: str = "unverified"
    observed_at: str | None = None

    def has_provenance(self) -> bool:
        return bool(self.evidence_id.strip() and self.source.strip())

@dataclass
class KnowledgeGraph:
    nodes: dict[str, dict[str, Any]] = field(default_factory=dict)
    edges: list[tuple[str, str, str]] = field(default_factory=list)

    def add_node(self, node_id: str, **attributes: Any) -> None:
        if not node_id or node_id in self.nodes:
            raise ValueError("node ID must be unique and non-empty")
        self.nodes[node_id] = dict(attributes)

    def add_edge(self, source: str, target: str, relation: str) -> None:
        if source not in self.nodes or target not in self.nodes:
            raise KeyError("both graph endpoints must exist")
        edge = (source, target, relation)
        if edge not in self.edges:
            self.edges.append(edge)

@dataclass(frozen=True)
class AgentResult:
    agent_id: str
    output: dict[str, Any]
    status: str = "completed"

class SacredAgent:
    agent_id = "BASE"
    purpose = "Base agent"
    capabilities = SAFE_CAPABILITIES

    def run(self, payload: dict[str, Any]) -> AgentResult:
        return AgentResult(self.agent_id, self.process(dict(payload)))

    def process(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

class AtomCoreAgent(SacredAgent):
    agent_id = "ATOM_CORE"
    purpose = "Decompose objectives into bounded work packages."
    def process(self, payload):
        objective = str(payload.get("objective", "")).strip()
        if not objective:
            raise ValueError("objective is required")
        return {"objective": objective, "work_packages": [
            "observe_and_scope", "map_known_context", "research_sources",
            "classify_evidence", "model_scenarios", "independent_validation",
            "prepare_report"]}

class FlowerMapAgent(SacredAgent):
    agent_id = "FLOWER_MAP"
    purpose = "Map knowledge, source, evidence, and dependency relationships."
    def process(self, payload):
        graph = KnowledgeGraph()
        for item in payload.get("evidence", []):
            if not isinstance(item, Evidence):
                raise TypeError("evidence entries must be Evidence objects")
            graph.add_node(item.evidence_id, source=item.source,
                           status=item.status, claim=item.claim)
        return {"nodes": graph.nodes, "edges": graph.edges,
                "node_count": len(graph.nodes)}

class MetatronGridAgent(SacredAgent):
    agent_id = "METATRON_GRID"
    purpose = "Resolve declared dependencies into a stable order."
    def process(self, payload):
        dependencies = payload.get("dependencies", {})
        ordered, visiting, visited = [], set(), set()
        def visit(name):
            if name in visiting:
                raise ValueError("dependency cycle detected")
            if name in visited:
                return
            if name not in dependencies:
                raise KeyError(f"unknown dependency: {name}")
            visiting.add(name)
            for dep in dependencies[name]:
                visit(dep)
            visiting.remove(name)
            visited.add(name)
            ordered.append(name)
        for name in sorted(dependencies):
            visit(name)
        return {"dependency_order": ordered}

class TorusFeedbackAgent(SacredAgent):
    agent_id = "TORUS_FEEDBACK"
    purpose = "Compare prior output with feedback without mutating sources."
    def process(self, payload):
        feedback = list(payload.get("feedback", []))
        return {"prior_output_present": payload.get("prior_output") is not None,
                "feedback_items": feedback,
                "next_step": "propose_revision_for_review" if feedback else "retain_current",
                "source_mutation": False}

class TesseractForesightAgent(SacredAgent):
    agent_id = "TESSERACT_FORESIGHT"
    purpose = "Produce bounded scenario prompts for horizons 1 through 10."
    def process(self, payload):
        subject = str(payload.get("subject", "objective")).strip() or "objective"
        return {"scenarios": [
            {"horizon": n, "question": f"What could change for {subject} by step {n}?",
             "status": "scenario_not_prediction"} for n in range(1, 11)]}

class DodecaCoordinatorAgent(SacredAgent):
    agent_id = "DODECA_COORDINATOR"
    purpose = "Aggregate specialist outputs and expose disagreement."
    def process(self, payload):
        results = payload.get("results", [])
        ids = [r.agent_id for r in results if isinstance(r, AgentResult)]
        return {"participating_agents": ids, "result_count": len(ids),
                "consensus": "not_assessed_without_explicit_evaluation"}

class IcosaAdaptiveAgent(SacredAgent):
    agent_id = "ICOSA_ADAPTIVE"
    purpose = "Generate alternatives without selecting or executing them."
    def process(self, payload):
        return {"alternatives": list(payload.get("options", [])),
                "selection": None, "execution": "disabled"}

class SpiralLearningAgent(SacredAgent):
    agent_id = "SPIRAL_LEARNING"
    purpose = "Track learning proposals without writing canonical memory."
    def process(self, payload):
        observations = list(payload.get("observations", []))
        return {"observations": observations,
                "learning_proposal": "review_required" if observations else "none",
                "canonical_memory_write": False}

class VesicaBridgeAgent(SacredAgent):
    agent_id = "VESICA_BRIDGE"
    purpose = "Identify cross-domain links for human review."
    def process(self, payload):
        domains = sorted(set(payload.get("domains", [])))
        pairs = [(domains[i], domains[j]) for i in range(len(domains))
                 for j in range(i + 1, len(domains))]
        return {"candidate_links": pairs, "links_are_hypotheses": True}

class ValidatorAgent(SacredAgent):
    agent_id = "PLATONIC_VALIDATORS"
    purpose = "Check evidence provenance and epistemic labels."
    def process(self, payload):
        checks = []
        for item in payload.get("evidence", []):
            if not isinstance(item, Evidence):
                checks.append({"valid": False, "reason": "invalid_record_type"})
                continue
            valid = item.has_provenance()
            checks.append({"evidence_id": item.evidence_id, "valid": valid,
                           "status": item.status,
                           "reason": "provenance_present" if valid else "missing_source_or_id"})
        return {"checks": checks, "all_valid": all(c["valid"] for c in checks)}

class OrbitalSchedulerAgent(SacredAgent):
    agent_id = "ORBITAL_SCHEDULER"
    purpose = "Prioritize a proposed queue; does not run background jobs."
    def process(self, payload):
        return {"queue": list(payload.get("tasks", [])), "mode": "proposal_only",
                "background_execution": False}

class CenterGovernorAgent(SacredAgent):
    agent_id = "CENTER_GOVERNOR"
    purpose = "Enforce objective, capability, and approval boundaries."
    def process(self, payload):
        requested = set(payload.get("requested_capabilities", ["read", "analyze", "report"]))
        denied = sorted(requested - SAFE_CAPABILITIES)
        return {"objective_present": bool(str(payload.get("objective", "")).strip()),
                "allowed_capabilities": sorted(requested & SAFE_CAPABILITIES),
                "denied_capabilities": denied, "external_action_authorized": False,
                "source_write_authorized": False}

class SacredAtomOrchestrator:
    """Deterministic dispatcher for registered, bounded specialist agents."""
    def __init__(self, agents: Iterable[SacredAgent] | None = None):
        roster = list(agents) if agents is not None else [
            AtomCoreAgent(), FlowerMapAgent(), MetatronGridAgent(),
            TorusFeedbackAgent(), TesseractForesightAgent(),
            DodecaCoordinatorAgent(), IcosaAdaptiveAgent(),
            SpiralLearningAgent(), VesicaBridgeAgent(), ValidatorAgent(),
            OrbitalSchedulerAgent(), CenterGovernorAgent()]
        self.agents = {}
        for agent in roster:
            if not agent.agent_id or agent.agent_id in self.agents:
                raise ValueError("agent IDs must be unique and non-empty")
            if not set(agent.capabilities).issubset(SAFE_CAPABILITIES):
                raise PermissionError("agent exceeds safe capability baseline")
            self.agents[agent.agent_id] = agent

    def run_agent(self, agent_id: str, payload: dict[str, Any]) -> AgentResult:
        if agent_id not in self.agents:
            raise KeyError(f"agent is not registered: {agent_id}")
        return self.agents[agent_id].run(payload)

    def status(self):
        return {"engine": "SACRED_ATOM_MULTI_AGENT",
                "state": "local_orchestration_library",
                "agents": [{"agent_id": a.agent_id, "purpose": a.purpose,
                            "capabilities": sorted(a.capabilities)}
                           for a in self.agents.values()],
                "subjective_consciousness_claim": False,
                "background_execution": False, "network_access": False,
                "source_mutation": False, "external_actions": False}
