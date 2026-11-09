"""PETS integration primitives: evidence, RBAC and explicit adapters."""
from .evidence_store import EvidenceStore
from .permissions import Role, Permission, authorize
from .adapters import AdapterRegistry, ReadOnlyAdapter
from .platforms import PlatformProfile, PlatformAdapterRegistry, detect_platform, supported_targets

__all__ = [
    "EvidenceStore", "Role", "Permission", "authorize",
    "AdapterRegistry", "ReadOnlyAdapter", "PlatformProfile",
    "PlatformAdapterRegistry", "detect_platform", "supported_targets",
]
