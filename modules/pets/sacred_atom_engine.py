"""Sacred Atom orchestration engine for PETS/AEGIS.

The geometry is an organizational metaphor, not a claim of machine consciousness.
Assembly is allowlist-only and never imports or executes downloaded code.
GPU acceleration is an injected optional backend; deterministic CPU fallback
is always available.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Protocol


class Layer(str, Enum):
    CENTER = "center"
    KNOWLEDGE = "knowledge"
    REASONING = "reasoning"
    VALIDATION = "validation"
    EXECUTION = "execution"
    PRESENTATION = "presentation"


@dataclass(frozen=True)
class AtomNode:
    node_id: str
    layer: Layer
    purpose: str
    dependencies: tuple[str, ...] = ()


@dataclass(frozen=True)
class ComponentSpec:
    component_id: str
    version: str
    dependencies: tuple[str, ...] = ()
    enabled: bool = True
    trusted: bool = False
    capabilities: tuple[str, ...] = ("read",)


class ComputeBackend(Protocol):
    name: str
    def map_values(self, values: list[float], operation: str) -> list[float]: ...


class CPUBackend:
    name = "cpu"
    def map_values(self, values: list[float], operation: str) -> list[float]:
        if operation == "identity":
            return list(values)
        if operation == "square":
            return [v * v for v in values]
        raise ValueError("unsupported compute operation")


@dataclass
class SacredAtomGUIState:
    """UI-neutral view model consumed by desktop/mobile GUI wrappers."""
    active_layer: str = Layer.CENTER.value
    status: str = "ready"
    selected_component: str | None = None
    notices: list[str] = field(default_factory=list)


class SacredAtomEngine:
    def __init__(self, nodes: tuple[AtomNode, ...] | None = None,
                 gpu_backend: ComputeBackend | None = None) -> None:
        self.nodes = nodes or self.default_geometry()
        self.cpu = CPUBackend()
        self.gpu = gpu_backend
        self.gui = SacredAtomGUIState()
        self._components: dict[str, ComponentSpec] = {}
        self._validate_geometry()

    @staticmethod
    def default_geometry() -> tuple[AtomNode, ...]:
        # Conscious center with multidirectional growth represented as layers.
        return (
            AtomNode("center", Layer.CENTER, "human-defined purpose and policy"),
            AtomNode("knowledge", Layer.KNOWLEDGE, "curated evidence and source graph", ("center",)),
            AtomNode("reasoning", Layer.REASONING, "bounded analysis and planning", ("knowledge",)),
            AtomNode("validation", Layer.VALIDATION, "tests, provenance and policy checks", ("reasoning",)),
            AtomNode("execution", Layer.EXECUTION, "approved deterministic operations", ("validation",)),
            AtomNode("presentation", Layer.PRESENTATION, "GUI state and reports", ("knowledge", "validation")),
        )

    def _validate_geometry(self) -> None:
        ids = [n.node_id for n in self.nodes]
        if len(ids) != len(set(ids)) or "center" not in ids:
            raise ValueError("geometry requires unique node IDs and a center")
        known = set(ids)
        for node in self.nodes:
            if any(dep not in known for dep in node.dependencies):
                raise ValueError(f"unknown dependency in {node.node_id}")
        # Detect cycles using depth-first traversal.
        visiting: set[str] = set(); visited: set[str] = set()
        graph = {n.node_id: n.dependencies for n in self.nodes}
        def visit(key: str) -> None:
            if key in visiting: raise ValueError("geometry dependency cycle")
            if key in visited: return
            visiting.add(key)
            for dep in graph[key]: visit(dep)
            visiting.remove(key); visited.add(key)
        for key in ids: visit(key)

    def register_component(self, spec: ComponentSpec) -> None:
        if not spec.component_id or spec.component_id in self._components:
            raise ValueError("component ID must be unique and non-empty")
        if not spec.trusted:
            raise PermissionError("component is not allowlisted as trusted")
        if any(cap not in {"read", "analyze", "report"} for cap in spec.capabilities):
            raise PermissionError("component requests a capability outside the safe baseline")
        self._components[spec.component_id] = spec

    def assemble_plan(self, requested: tuple[str, ...] | None = None) -> tuple[str, ...]:
        """Resolve dependencies for explicitly registered components; no code execution."""
        wanted = set(requested or self._components.keys())
        ordered: list[str] = []; visiting: set[str] = set(); visited: set[str] = set()
        def visit(cid: str) -> None:
            if cid not in self._components:
                raise KeyError(f"component is not registered: {cid}")
            if cid in visiting: raise ValueError("component dependency cycle")
            if cid in visited: return
            spec = self._components[cid]
            if not spec.enabled: raise PermissionError(f"component disabled: {cid}")
            visiting.add(cid)
            for dep in spec.dependencies: visit(dep)
            visiting.remove(cid); visited.add(cid); ordered.append(cid)
        for cid in sorted(wanted): visit(cid)
        self.gui.status = "assembly_plan_ready"
        self.gui.notices.append("Plan resolved; no component code was executed.")
        return tuple(ordered)

    def compute(self, values: list[float], operation: str = "identity") -> tuple[str, list[float]]:
        """Try the explicitly injected GPU backend; fall back safely to CPU."""
        if self.gpu is not None:
            try:
                return self.gpu.name, self.gpu.map_values(values, operation)
            except Exception as exc:
                self.gui.notices.append(f"GPU backend unavailable; CPU fallback used ({type(exc).__name__}).")
        return self.cpu.name, self.cpu.map_values(values, operation)

    def status(self) -> dict[str, Any]:
        return {
            "model": "Sacred Atom orchestration metaphor; not conscious",
            "center": "human-defined purpose and policy",
            "layers": [n.layer.value for n in self.nodes],
            "registered_components": sorted(self._components),
            "gpu_backend": self.gpu.name if self.gpu else None,
            "fallback_backend": self.cpu.name,
            "gui": {
                "active_layer": self.gui.active_layer,
                "status": self.gui.status,
                "selected_component": self.gui.selected_component,
                "notices": list(self.gui.notices),
            },
        }
