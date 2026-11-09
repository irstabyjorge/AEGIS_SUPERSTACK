"""Deterministic Sacred Atom knowledge geometry.

A geometric metaphor for organizing software capabilities; not a model of
sentience or a claim that software is conscious.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import cos, pi, sin
from typing import Iterable

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
    """One center, six inner functions and twelve outer capability domains."""
    CENTER = ("conscious_center", "governance", 0.0, 0.0, "Coordination metaphor: goals, state and human authorization")
    INNER = (
        ("knowledge", "knowledge", "Curated knowledge and provenance"),
        ("reasoning", "reasoning", "Structured analysis and validation"),
        ("memory", "memory", "User-approved project state and durable records"),
        ("compute", "compute", "CPU/GPU backend selection"),
        ("interfaces", "interfaces", "GUI, CLI and platform bridges"),
        ("guardrails", "security", "Permissions, policy and safety checks"),
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
        nodes = [AtomNode(self.CENTER[0], self.CENTER[1], 0.0, 0.0, 0.0, 0.0, self.CENTER[4])]
        for i, (node_id, layer, desc) in enumerate(self.INNER):
            angle = 2 * pi * i / len(self.INNER)
            nodes.append(AtomNode(node_id, layer, angle, 1.0, cos(angle), sin(angle), desc))
        for i, (node_id, layer) in enumerate(self.OUTER):
            angle = 2 * pi * i / len(self.OUTER)
            nodes.append(AtomNode(node_id, layer, angle, 2.0, 2*cos(angle), 2*sin(angle), f"{layer} capability domain: {node_id}"))
        self.nodes = tuple(nodes)
        edges = []
        inner_ids = [x[0] for x in self.INNER]
        outer_ids = [x[0] for x in self.OUTER]
        for node_id in inner_ids:
            edges.append(AtomEdge("conscious_center", node_id, "governs"))
        for i, node_id in enumerate(outer_ids):
            edges.append(AtomEdge(inner_ids[i % len(inner_ids)], node_id, "coordinates"))
            edges.append(AtomEdge("conscious_center", node_id, "authorizes"))
        self.edges = tuple(edges)
        self._node_ids = {node.node_id for node in self.nodes}

    def validate(self) -> bool:
        return (
            len(self._node_ids) == len(self.nodes)
            and all(e.source in self._node_ids and e.target in self._node_ids for e in self.edges)
            and any(n.node_id == "conscious_center" and n.radius == 0 for n in self.nodes)
        )

    def snapshot(self) -> dict:
        return {
            "model": "sacred_atom_geometry_v1",
            "interpretation": "organizational metaphor; not machine consciousness",
            "center": "conscious_center",
            "nodes": [n.__dict__ for n in self.nodes],
            "edges": [e.__dict__ for e in self.edges],
            "valid": self.validate(),
        }
