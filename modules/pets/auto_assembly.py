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
        visiting: list[str] = []
        visited: set[str] = set()
        blocked: dict[str, str] = {}

        def visit(name: str) -> bool:
            if name in visited:
                return True
            if name in visiting:
                start = visiting.index(name)
                for cycle_name in visiting[start:]:
                    blocked[cycle_name] = "dependency cycle"
                blocked[name] = "dependency cycle"
                return False
            component = self.components.get(name)
            if component is None:
                blocked[name] = "component not registered"
                return False
            visiting.append(name)
            dependencies_ok = True
            for dep in component.dependencies:
                if not visit(dep):
                    dependencies_ok = False
            visiting.pop()
            if not dependencies_ok or name in blocked:
                blocked.setdefault(name, "one or more dependencies are blocked")
                return False
            if not component.trusted or not component.tests_passed:
                blocked[name] = "requires trusted provenance and passing tests"
                return False
            visited.add(name)
            order.append(name)
            return True

        for name in requested:
            visit(name)
        return {
            "mode": "plan_only",
            "execution_performed": False,
            "approved_order": order,
            "blocked": blocked,
            "requires_human_approval": bool(order),
            "note": "No downloads, installs, imports, shell commands or code execution are performed by the planner.",
        }
