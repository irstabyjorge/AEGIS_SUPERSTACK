"""PETS integration primitives: evidence, RBAC and explicit adapters."""
from .evidence_store import EvidenceStore
from .permissions import Role, Permission, authorize
from .adapters import AdapterRegistry, ReadOnlyAdapter
from .platforms import PlatformProfile, PlatformAdapterRegistry, detect_platform, supported_targets
from .sacred_atom import SacredAtomGraph
from .compute_engine import ComputeEngine
from .auto_assembly import AssemblyPlanner, Component
from .sacred_atom_engine import SacredAtomEngine, AtomNode, Layer, ComponentSpec, CPUBackend

__all__ = [
    "EvidenceStore", "Role", "Permission", "authorize",
    "AdapterRegistry", "ReadOnlyAdapter", "PlatformProfile",
    "PlatformAdapterRegistry", "detect_platform", "supported_targets",
    "SacredAtomGraph", "ComputeEngine", "AssemblyPlanner", "Component",
    "SacredAtomEngine", "AtomNode", "Layer", "ComponentSpec", "CPUBackend",
]
