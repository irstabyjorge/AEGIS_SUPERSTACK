"""Provider adapter contracts.

Adapters are intentionally read-only. Host ChatGPT connectors are not
automatically available to a separately deployed PETS process; a provider
adapter needs its own approved API integration and runtime credentials.
"""
from __future__ import annotations

from typing import Any, Protocol


class ReadOnlyAdapter(Protocol):
    provider: str
    read_operations: frozenset[str]

    def health(self) -> dict[str, Any]: ...
    def read(self, operation: str, params: dict[str, Any]) -> dict[str, Any]: ...


class AdapterRegistry:
    def __init__(self):
        self._adapters: dict[str, ReadOnlyAdapter] = {}

    def register(self, adapter: ReadOnlyAdapter) -> None:
        provider = getattr(adapter, "provider", "")
        if not isinstance(provider, str) or not provider or provider in self._adapters:
            raise ValueError("invalid_or_duplicate_provider")
        if not callable(getattr(adapter, "health", None)) or not callable(
            getattr(adapter, "read", None)
        ):
            raise TypeError("adapter_contract_not_satisfied")
        operations = getattr(adapter, "read_operations", None)
        if (
            not isinstance(operations, (set, frozenset, tuple, list))
            or not operations
            or any(
                not isinstance(item, str)
                or not item
                or item != item.strip()
                or item != item.lower()
                for item in operations
            )
        ):
            raise TypeError("adapter_read_operations_allowlist_required")
        self._adapters[provider] = adapter

    def health(self) -> dict[str, dict[str, Any]]:
        return {name: adapter.health() for name, adapter in sorted(self._adapters.items())}

    def read(
        self, provider: str, operation: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        if provider not in self._adapters:
            raise KeyError("provider_not_registered")
        if not isinstance(operation, str):
            raise PermissionError("read_only_adapter")
        normalized = operation.strip().lower()
        if not normalized or normalized != operation.strip():
            raise PermissionError("read_only_adapter")
        adapter = self._adapters[provider]
        mutation_verbs = {
            "create", "update", "patch", "delete", "remove", "send", "write",
            "deploy", "execute", "mutate", "put", "post", "upload", "revoke",
            "grant", "set", "insert",
        }
        operation_tokens = set(normalized.replace("/", "_").replace(":", "_").replace("-", "_").replace(".", "_").split("_"))
        if operation_tokens & mutation_verbs or normalized not in adapter.read_operations:
            raise PermissionError("read_only_adapter")
        if params is not None and not isinstance(params, dict):
            raise ValueError("params_must_be_object")
        result = adapter.read(normalized, params or {})
        if not isinstance(result, dict):
            raise TypeError("adapter_result_must_be_object")
        return result


class FixtureAdapter:
    """Deterministic test adapter; performs no network access."""

    def __init__(self, provider: str, fixtures: dict[str, dict[str, Any]]):
        self.provider = provider
        self._fixtures = fixtures
        self.read_operations = frozenset(fixtures)

    def health(self) -> dict[str, Any]:
        return {"status": "ok", "mode": "fixture_read_only"}

    def read(self, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        if operation not in self.read_operations:
            raise KeyError("operation_not_available")
        return {"provider": self.provider, "data": self._fixtures[operation]}
