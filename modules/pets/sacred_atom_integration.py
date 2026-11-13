"""Additive bridge between Sacred Atom geometry and bounded agents.

The graph supplies organizational structure; the orchestrator performs
explicitly requested read/analyze/report tasks. Neither component executes
external actions or mutates source data.
"""
from __future__ import annotations

from modules.pets.sacred_atom_agents import KnowledgeGraph, SacredAtomOrchestrator
from modules.pets.sacred_atom_geometry import SacredAtomGraph


class SacredAtomSystem:
    """Unified read-only facade over geometry and specialist orchestration."""

    def __init__(self) -> None:
        self.geometry = SacredAtomGraph()
        self.orchestrator = SacredAtomOrchestrator()

    def geometry_knowledge_graph(self) -> KnowledgeGraph:
        if not self.geometry.validate():
            raise ValueError("Sacred Atom geometry failed validation")
        graph = KnowledgeGraph()
        for node in self.geometry.nodes:
            graph.add_node(
                node.node_id,
                layer=node.layer,
                radius=node.radius,
                angle_radians=node.angle_radians,
                x=node.x,
                y=node.y,
                description=node.description,
                source_model="sacred_atom_geometry_v1",
            )
        for edge in self.geometry.edges:
            graph.add_edge(edge.source, edge.target, edge.relation)
        return graph

    def run_agent(self, agent_id: str, payload: dict):
        return self.orchestrator.run_agent(agent_id, payload)

    def status(self) -> dict:
        return {
            "system": "PETS_AEGIS_SACRED_ATOM",
            "geometry": self.geometry.snapshot(),
            "orchestration": self.orchestrator.status(),
            "integration": "geometry_to_knowledge_graph_adapter",
            "external_actions": False,
            "source_mutation": False,
        }
