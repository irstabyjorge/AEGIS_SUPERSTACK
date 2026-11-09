"""PETS integration primitives: local evidence, RBAC and read-only adapters."""
from .evidence_store import EvidenceStore
from .permissions import Role, Permission, authorize
from .adapters import AdapterRegistry, ReadOnlyAdapter

__all__ = ["EvidenceStore", "Role", "Permission", "authorize", "AdapterRegistry", "ReadOnlyAdapter"]
