"""Plan-only capability assembler; never imports or executes candidate code."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable

@dataclass(frozen=True)
class Component:
    component_id: str
    version: str
    dependencies: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ()
    trusted: bool = False
    tests_passed: bool = False

class AssemblyPlanner:
    def __init__(self, components: Iterable[Component]):
        items = list(components)
        self.components = {c.component_id: c for c in items}
        if len(self.components) != len(items):
            raise ValueError("component ids must be unique")
    def plan(self, requested: Iterable[str]) -> dict:
        order: list[str] = []
        visiting: set[str] = set()
        visited: set[str] = set()
        blocked: dict[str, str] = {}
        def visit(name: str) -> None:
            if name in visited: return
            if name in visiting:
                blocked[name] = "dependency cycle"; return
            component = self.components.get(name)
            if component is None:
                blocked[name] = "component not registered"; return
            visiting.add(name)
            for dep in component.dependencies: visit(dep)
            visiting.remove(name)
            if name not in blocked and component.trusted and component.tests_passed:
                visited.add(name); order.append(name)
            else:
                blocked.setdefault(name, "requires trusted provenance and passing tests")
        for name in requested: visit(name)
        return {
            "mode": "plan_only",
            "execution_performed": False,
            "approved_order": order,
            "blocked": blocked,
            "requires_human_approval": bool(order),
            "note": "No downloads, installs, imports, shell commands or code execution are performed by the planner.",
        }
