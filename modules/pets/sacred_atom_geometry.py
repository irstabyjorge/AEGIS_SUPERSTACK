"""Deterministic Sacred Atom geometry for PETS/AEGIS.

The geometry is a software-organization metaphor, not a claim of sentience
or a physical/scientific law. This module has no I/O or external effects.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from math import cos, pi, sin


@dataclass(frozen=True)
class AtomNode:
    node_id: str
    layer: str
    angle_radians: float
    radius: float
    x: float
    y: float
    description: str


@dataclass(frozen=True)
class AtomEdge:
    source: str
    target: str
    relation: str


class SacredAtomGraph:
    """One governance center, six inner functions, and twelve outer domains."""

    CENTER = (
        "conscious_center",
        "governance",
        "Human-defined purpose, policy, and authorization",
    )
    INNER = (
        ("knowledge", "knowledge", "Curated knowledge and provenance"),
        ("reasoning", "reasoning", "Structured analysis and validation"),
        ("memory", "memory", "Approved project state and durable records"),
        ("compute", "compute", "Bounded computation"),
        ("interfaces", "interfaces", "User-facing interfaces and adapters"),
        ("guardrails", "security", "Permissions, policy, and safety checks"),
    )
    OUTER = (
        ("research", "research"), ("evidence", "evidence"),
        ("reports", "reports"), ("automation", "automation"),
        ("linux", "platform"), ("windows", "platform"),
        ("macos_apple", "platform"), ("android", "platform"),
        ("ios_ipados", "platform"), ("iot_gateways", "hardware"),
        ("arm_riscv", "hardware"), ("integrations", "connectors"),
    )

    def __init__(self) -> None:
        center_id, center_layer, center_desc = self.CENTER
        nodes = [AtomNode(center_id, center_layer, 0.0, 0.0, 0.0, 0.0, center_desc)]
        for index, (node_id, layer, description) in enumerate(self.INNER):
            angle = 2 * pi * index / len(self.INNER)
            nodes.append(AtomNode(node_id, layer, angle, 1.0,
                                  cos(angle), sin(angle), description))
        for index, (node_id, layer) in enumerate(self.OUTER):
            angle = 2 * pi * index / len(self.OUTER)
            nodes.append(AtomNode(node_id, layer, angle, 2.0,
                                  2 * cos(angle), 2 * sin(angle),
                                  f"{layer} capability domain: {node_id}"))
        self.nodes = tuple(nodes)
        inner_ids = [entry[0] for entry in self.INNER]
        edges = [AtomEdge(center_id, node_id, "governs") for node_id in inner_ids]
        for index, (node_id, _) in enumerate(self.OUTER):
            edges.append(AtomEdge(inner_ids[index % len(inner_ids)], node_id, "coordinates"))
            edges.append(AtomEdge(center_id, node_id, "policy_boundary"))
        self.edges = tuple(edges)
        self._node_ids = frozenset(node.node_id for node in self.nodes)

    def validate(self) -> bool:
        return (
            len(self._node_ids) == len(self.nodes)
            and all(edge.source in self._node_ids and edge.target in self._node_ids
                    for edge in self.edges)
            and self.nodes[0].node_id == self.CENTER[0]
            and self.nodes[0].radius == 0.0
        )

    def snapshot(self) -> dict:
        return {
            "model": "sacred_atom_geometry_v1",
            "interpretation": "organizational metaphor; not machine consciousness",
            "center": self.CENTER[0],
            "nodes": [asdict(node) for node in self.nodes],
            "edges": [asdict(edge) for edge in self.edges],
            "valid": self.validate(),
        }
